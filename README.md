
# Quiz API Project

## Overview
This is a Quiz API built using FastAPI. The application provides functionalities to manage quizzes, upload documents, fetch analytics, and more. It is designed to work with a PostgreSQL database and is deployed on Render.

---

## Features
- Create, retrieve, and manage quizzes.
- Upload and search documents.
- Fetch analytics for quizzes and users.

---

## Installation and Deployment

### Prerequisites
1. Python 3.10+
2. PostgreSQL database
3. Dependencies from `requirements.txt`
4. A `.env` file containing:<br>
   ```
   DATABASE_URL=postgresql+asyncpg://<username>:<password>@<hostname>/<database>
   OPENAI_API_KEY=<your chatgpt key>
   ```

### Local Setup
1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up the `.env` file with your database credentials.
4. Run the application locally:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 3000
   ```

### Deployment on Render
1. Create a new **Web Service** on Render.
2. Add your GitHub repository and set the build command:
   ```
   pip install -r requirements.txt
   ```
3. Set the start command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 3000
   ```
4. Link a managed PostgreSQL instance on Render.
5. Add the `OPENAI_API_KEY` and `DATABASE_URL` environment variable in the Render service settings with the PostgreSQL URL.

---

## API Documentation

### Quiz Management

#### 1. Create Quiz
- **URL:** `POST /api/quiz/create`
- **Body:**
  ```json
  {
    "name": "SEO 101",
    "difficulty": "medium",
    "topic": "search engine optimization",
    "file_ids": ["file123", "file456"],
    "number_of_questions": 10,
    "question_type": "mcq",
    "custom_instructions": "Focus on practical applications"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "Quiz created successfully.",
    "quiz_id": "1234-abcd-5678-efgh"
  }
  ```

#### 2. Get Quiz
- **URL:** `GET /api/quiz/get/{quiz_id}`
- **Response:**
  ```json
  {
    "success": true,
    "message": "Quiz details retrieved successfully.",
    "data": {
      "quiz_id": "1234-abcd",
      "name": "SEO 101",
      "difficulty": "medium",
      "topic": "search engine optimization",
      "questions": [
        {
          "question_id": "q1",
          "question": "What is SEO?",
          "options": ["A", "B", "C", "D"]
        }
      ]
    }
  }
  ```

#### 3. Submit Quiz
- **URL:** `POST /api/quiz/{quiz_id}/submit`
- **Body:**
  ```json
  {
    "answers": [
      {"question_id": "q1", "selected_answer": "A"}
    ]
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "Quiz submitted successfully.",
    "score": 5,
    "percentage": 50
  }
  ```

#### 4. Get All Quizzes
- **URL:** `GET /api/quiz/get-all?page=1&limit=10`
- **Response:**
  ```json
  {
    "success": true,
    "data": [
      {
        "quiz_id": "1234-abcd",
        "name": "SEO 101",
        "topic": "search engine optimization"
      }
    ]
  }
  ```

---

### Document Management

#### 1. Upload File
- **URL:** `POST /api/files/upload`
- **Form Data:** A file (PDF or TXT).

#### 2. Search Files
- **URL:** `GET /api/files/search?q=keyword&page=1&limit=10`
- **Response:** Lists matching documents.

---

### Analytics

#### 1. Quiz Analytics
- **URL:** `GET /api/analytics/quiz/{quiz_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- **Response:** Analytics on quiz submissions.

#### 2. User Analytics
- **URL:** `GET /api/analytics/user/{user_id}`
- **Response:** Analytics for a specific user.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.
