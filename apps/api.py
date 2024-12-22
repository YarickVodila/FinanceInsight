from os import getenv
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from rag_system.rag_pipeline import FinanceMultiAgentRAG


class Query(BaseModel):
    content: str


load_dotenv(override=True)
app = FastAPI()
rag_agent = FinanceMultiAgentRAG(getenv("MISTRAL_API_KEY"))


@app.get("/healthcheck/")
def healthcheck() -> Dict[str, str]:
    return {"status": "health"}


@app.post("/generate/")
def get_response(query: Query) -> Dict[str, str]:
    try:
        model_answer = rag_agent.get_response(query.content)
    except Exception:
        model_answer = ""
    return {"response": model_answer}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
