import os
import uuid
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Quiz, Question, Document, Submission
from app.database import get_db
from openai import OpenAI
from sqlalchemy import func

router = APIRouter()

# Load environment variables
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# Define the input schema
class QuizCreateRequest(BaseModel):
    name: str
    difficulty: str
    topic: str
    file_ids: list[str]
    number_of_questions: int
    question_type: str
    custom_instructions: str

@router.post("/quiz/create", summary="Create a quiz")
async def create_quiz(payload: QuizCreateRequest, db: AsyncSession = Depends(get_db)):
    # Validate file IDs
    query = await db.execute(select(Document).where(Document.file_id.in_(payload.file_ids)))
    documents = query.scalars().all()
    if not documents or len(documents) != len(payload.file_ids):
        raise HTTPException(status_code=400, detail="One or more file IDs are invalid.")

    # Combine content from all files
    combined_content = "\n\n".join(doc.content for doc in documents if doc.content)

    # Prepare prompt for OpenAI API
    prompt = f"""
You are a quiz generator for educational purposes.
Create a {payload.number_of_questions}-question quiz on the topic "{payload.topic}" with difficulty "{payload.difficulty}".
The quiz should contain only "{payload.question_type}" questions.

The quiz should focus on practical applications and the following content:

{combined_content}

Instructions:
- If the question type is "mcq":
  - Ensure every question has exactly 4 options (A, B, C, D).
  - Clearly indicate the correct answer as one of the options in the field "correct_answer".
  - The "correct_answer" must match exactly with one of the options provided.
- If the question type is "true/false":
  - Ensure every question has only 2 options: ["True", "False"].
  - Clearly indicate the correct answer as either "True" or "False" in the field "correct_answer".
  - The "correct_answer" must match exactly with one of the options provided.
- Do not mix question types. Only include the type specified in "{payload.question_type}".
- Ensure the questions and answers are consistent with the specified topic and difficulty level.

Output format:
Return the quiz as a JSON array in the following format:
[
    {{
        "question_id": "q1",
        "question": "What is SEO?",
        "options": ["A. Search Engine Optimization", "B. Search Engine Operation", "C. Software Engineering Optimization", "D. None of the above"],
        "correct_answer": "A"
    }},
    {{
        "question_id": "q2",
        "question": "Python is a programming language.",
        "options": ["True", "False"],
        "correct_answer": "True"
    }},
    ...
]

Important Notes:
1. Every question must include a valid "correct_answer" field that matches one of the options exactly.
2. Do NOT add any commentary, explanation, or text outside of the specified JSON format.
"""



    try:
        # Use OpenAI's updated API
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert quiz generator."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4",  # Use "gpt-4" or "gpt-3.5-turbo" depending on availability
        )
        
        # Extract the response content properly
        print(response.choices[0].message.content)
        response_content = response.choices[0].message.content.strip()
        generated_questions = eval(response_content)  # Convert JSON-like string to Python object
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    # Validate the response
    if not isinstance(generated_questions, list) or len(generated_questions) != payload.number_of_questions:
        raise HTTPException(status_code=500, detail="Invalid response from OpenAI.")

    # Save the quiz and questions to the database
    quiz_id = str(uuid.uuid4())
    new_quiz = Quiz(
        quiz_id=quiz_id,
        name=payload.name,
        difficulty=payload.difficulty,
        topic=payload.topic,
        number_of_questions=payload.number_of_questions,
        question_type=payload.question_type,
        custom_instructions=payload.custom_instructions,
    )
    db.add(new_quiz)

    for index, question in enumerate(generated_questions, start=1):
        unique_question_id = f"{quiz_id}_q{index}"  # Ensure question_id is unique
        new_question = Question(
            question_id=unique_question_id,  # Unique question ID
            quiz_id=quiz_id,
            question=question["question"],
            options=json.dumps(question["options"]),  # Serialize options to JSON string
            correct_answer=question["correct_answer"],
        )
        db.add(new_question)

    await db.commit()

    # Return the quiz ID
    return {
        "success": True,
        "message": "Quiz created successfully.",
        "quiz_id": quiz_id,
    }

@router.get("/quiz/get/{quiz_id}", summary="Get quiz details by quiz ID")
async def get_quiz(quiz_id: str, db: AsyncSession = Depends(get_db)):
    # Query the quiz by its ID
    quiz_query = await db.execute(select(Quiz).where(Quiz.quiz_id == quiz_id))
    quiz = quiz_query.scalars().first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Query the questions associated with the quiz
    questions_query = await db.execute(select(Question).where(Question.quiz_id == quiz_id))
    questions = questions_query.scalars().all()

    # Format the response
    response = {
        "quiz_id": quiz.quiz_id,
        "name": quiz.name,
        "difficulty": quiz.difficulty,
        "topic": quiz.topic,
        "number_of_questions": quiz.number_of_questions,
        "question_type": quiz.question_type,
        "custom_instructions": quiz.custom_instructions,
        "questions": [
            {
                "question_id": question.question_id,
                "question": question.question,
                "options": question.options,
            }
            for question in questions
        ]
    }

    return {
        "success": True,
        "message": "Quiz details retrieved successfully.",
        "data": response
    }

@router.get("/quiz/get-all", summary="Get all quizzes with pagination")
async def get_all_quizzes(
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    # Validate page and limit
    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Page and limit must be positive integers."
        )

    # Calculate offset
    offset = (page - 1) * limit

    # Fetch quizzes with pagination
    query = await db.execute(
        select(Quiz)
        .order_by(Quiz.quiz_id.desc())  # Replace created_at with quiz_id if not present
        .offset(offset)
        .limit(limit)
    )
    quizzes = query.scalars().all()

    # Fetch total count for pagination
    total_query = await db.execute(select(func.count()).select_from(Quiz))
    total_items = total_query.scalar()

    # Format response
    quizzes_data = [
        {
            "quiz_id": quiz.quiz_id,
            "name": quiz.name,
            "difficulty": quiz.difficulty,
            "topic": quiz.topic,
            "number_of_questions": quiz.number_of_questions,
            "question_type": quiz.question_type,
            "custom_instructions": quiz.custom_instructions,
            "created_at": getattr(quiz, "created_at", None),  # Include created_at if it exists
        }
        for quiz in quizzes
    ]

    return {
        "success": True,
        "message": "Quizzes retrieved successfully.",
        "data": quizzes_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
        },
    }

class SubmitQuizRequest(BaseModel):
    answers: list[dict]  # List of answers {question_id, selected_answer}

@router.post("/quiz/{quiz_id}/submit", summary="Submit a quiz")
async def submit_quiz(quiz_id: str, payload: SubmitQuizRequest, db: AsyncSession = Depends(get_db)):
    # Check if the quiz exists
    quiz_query = await db.execute(select(Quiz).where(Quiz.quiz_id == quiz_id))
    quiz = quiz_query.scalars().first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Validate the provided answers
    question_ids = [answer["question_id"] for answer in payload.answers]
    questions_query = await db.execute(
        select(Question).where(
            Question.quiz_id == quiz_id,
            Question.question_id.in_(question_ids)
        )
    )
    questions = questions_query.scalars().all()
    if len(questions) != len(payload.answers):
        raise HTTPException(status_code=400, detail="Some questions do not belong to this quiz")

    # Prepare submission and calculate score
    submissions = []
    score = 0
    total_questions = len(payload.answers)
    user_id = str(uuid.uuid4())  # Replace with actual user ID from authentication
    for answer in payload.answers:
        question = next(q for q in questions if q.question_id == answer["question_id"])
        is_correct = question.correct_answer == answer["selected_answer"]
        if is_correct:
            score += 1

        submissions.append(
            Submission(
                submission_id=str(uuid.uuid4()),
                quiz_id=quiz_id,  # String type
                user_id=user_id,
                question_id=answer["question_id"],
                selected_answer=answer["selected_answer"],
                is_correct=is_correct,
                created_at=func.now(),
            )
        )

    # Save submissions to the database
    db.add_all(submissions)
    await db.commit()

    # Return results
    return {
        "success": True,
        "message": "Quiz submitted successfully.",
        "quiz_id": quiz_id,
        "score": score,
        "total_questions": total_questions,
        "percentage": round((score / total_questions) * 100, 2),
    }


@router.get("/quizzes/{quiz_id}/results", summary="Get results for a specific quiz")
async def get_quiz_results(quiz_id: str, db: AsyncSession = Depends(get_db)):
    # Check if the quiz exists
    quiz_query = await db.execute(select(Quiz).where(Quiz.quiz_id == quiz_id))
    quiz = quiz_query.scalars().first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Fetch all submissions for the quiz
    submissions_query = await db.execute(
        select(Submission).where(Submission.quiz_id == quiz_id)
    )
    submissions = submissions_query.scalars().all()

    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions found for this quiz")

    # Organize submissions by user
    results_by_user = {}
    for submission in submissions:
        user_id = submission.user_id
        if user_id not in results_by_user:
            results_by_user[user_id] = {
                "user_id": user_id,
                "quiz_id": quiz_id,
                "score": 0,
                "total_questions": 0,
                "percentage": 0.0,
                "answers": []
            }
        # Update the user's result data
        results_by_user[user_id]["answers"].append({
            "question_id": submission.question_id,
            "selected_answer": submission.selected_answer,
            "is_correct": submission.is_correct
        })
        results_by_user[user_id]["total_questions"] += 1
        if submission.is_correct:
            results_by_user[user_id]["score"] += 1

    # Calculate percentage for each user
    for user_result in results_by_user.values():
        user_result["percentage"] = round(
            (user_result["score"] / user_result["total_questions"]) * 100, 2
        )

    # Format the results as a list
    results = list(results_by_user.values())

    return {
        "success": True,
        "message": "Quiz results retrieved successfully.",
        "quiz_id": quiz_id,
        "results": results
    }