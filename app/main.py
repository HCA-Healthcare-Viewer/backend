from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from app.api.routes import router as api_router



app = FastAPI()
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the HL7 Parser API!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)