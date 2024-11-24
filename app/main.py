from fastapi import FastAPI
from app.routers import documents, quizzes, analytics
from app.database import Base, engine

# Initialize database
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await create_tables()


app.include_router(documents.router, tags=["Documents"])
app.include_router(quizzes.router, prefix="/api", tags=["Quizzes"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])