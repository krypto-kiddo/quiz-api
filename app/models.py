from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.expression import func
from sqlalchemy.schema import Index
from app.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid 

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    search_vector = Column(TSVECTOR)

# Add an index for full-text search
Index("ix_documents_search_vector", Document.search_vector, postgresql_using="gin")

class Quiz(Base):
    __tablename__ = "quizzes"

    quiz_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    number_of_questions = Column(Integer, nullable=False)
    question_type = Column(String, nullable=False)
    custom_instructions = Column(Text, nullable=True)
    questions = relationship("Question", back_populates="quiz")
    created_at = Column(DateTime, default=func.now(), nullable=False)


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(String, primary_key=True, index=True)
    quiz_id = Column(String, ForeignKey("quizzes.quiz_id"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON string or similar
    correct_answer = Column(String, nullable=False)
    quiz = relationship("Quiz", back_populates="questions")

class Submission(Base):
    __tablename__ = "quiz_submissions"

    submission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(String, nullable=False)  # Changed to String
    user_id = Column(UUID(as_uuid=True), nullable=False)
    question_id = Column(String, nullable=False)
    selected_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=func.now())
