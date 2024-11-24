from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.models import Quiz, Submission, Question
from app.database import get_db
from datetime import datetime

router = APIRouter()

@router.get("/analytics/quiz/{quiz_id}", summary="Get analytics for a specific quiz")
async def get_quiz_analytics(
    quiz_id: str,
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
):
    # Check if the quiz exists
    quiz_query = await db.execute(select(Quiz).where(Quiz.quiz_id == quiz_id))
    quiz = quiz_query.scalars().first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Parse and validate date range
    try:
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Build query to fetch relevant submissions
    submissions_query = select(Submission).where(Submission.quiz_id == quiz_id)
    if start_datetime:
        submissions_query = submissions_query.where(Submission.created_at >= start_datetime)
    if end_datetime:
        submissions_query = submissions_query.where(Submission.created_at <= end_datetime)

    submissions_query = await db.execute(submissions_query)
    submissions = submissions_query.scalars().all()

    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions found for this quiz in the given date range")

    # Calculate analytics
    total_submissions = len(submissions)
    total_correct = sum(submission.is_correct for submission in submissions)
    question_stats = {}

    # Prepare stats per question
    for submission in submissions:
        question_id = submission.question_id
        if question_id not in question_stats:
            question_stats[question_id] = {
                "question_id": question_id,
                "total_attempts": 0,
                "correct_attempts": 0
            }
        question_stats[question_id]["total_attempts"] += 1
        if submission.is_correct:
            question_stats[question_id]["correct_attempts"] += 1

    # Convert question stats to a list and calculate percentages
    question_stats_list = [
        {
            **stats,
            "accuracy_percentage": round((stats["correct_attempts"] / stats["total_attempts"]) * 100, 2)
        }
        for stats in question_stats.values()
    ]

    # Prepare response
    return {
        "success": True,
        "message": "Quiz analytics retrieved successfully.",
        "quiz_id": quiz_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_submissions": total_submissions,
        "total_correct": total_correct,
        "accuracy_percentage": round((total_correct / total_submissions) * 100, 2) if total_submissions > 0 else 0.0,
        "question_stats": question_stats_list
    }


@router.get("/analytics/user/{user_id}", summary="Get analytics for a specific user")
async def get_user_analytics(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Build query to fetch all submissions by the user
    submissions_query = select(Submission).where(Submission.user_id == user_id)
    submissions_query = await db.execute(submissions_query)
    submissions = submissions_query.scalars().all()

    if not submissions:
        raise HTTPException(status_code=404, detail="No submissions found for this user")

    # Calculate user analytics
    total_attempted_quizzes = len(set(submission.quiz_id for submission in submissions))
    total_submissions = len(submissions)
    total_correct = sum(submission.is_correct for submission in submissions)
    accuracy_percentage = round((total_correct / total_submissions) * 100, 2) if total_submissions > 0 else 0.0

    # Prepare stats per quiz
    quiz_stats = {}
    for submission in submissions:
        quiz_id = submission.quiz_id
        if quiz_id not in quiz_stats:
            quiz_stats[quiz_id] = {
                "quiz_id": quiz_id,
                "total_attempts": 0,
                "correct_attempts": 0
            }
        quiz_stats[quiz_id]["total_attempts"] += 1
        if submission.is_correct:
            quiz_stats[quiz_id]["correct_attempts"] += 1

    # Convert quiz stats to a list and calculate percentages
    quiz_stats_list = [
        {
            **stats,
            "accuracy_percentage": round((stats["correct_attempts"] / stats["total_attempts"]) * 100, 2)
        }
        for stats in quiz_stats.values()
    ]

    # Prepare response
    return {
        "success": True,
        "message": "User analytics retrieved successfully.",
        "user_id": user_id,
        "total_attempted_quizzes": total_attempted_quizzes,
        "total_submissions": total_submissions,
        "total_correct": total_correct,
        "accuracy_percentage": accuracy_percentage,
        "quiz_stats": quiz_stats_list
    }
