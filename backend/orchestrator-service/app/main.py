import httpx
from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

PARSER_URL = os.getenv("PARSER_URL")

@app.post("/process")
async def process_resume(data: dict):

    file_path = data.get("file_url")

    try:
        # Send file as multipart
        with open(file_path, "rb") as f:
            files = {
                "file": (file_path.split("/")[-1], f)
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    PARSER_URL,
                    files=files
                )

        return {
            "status": "success",
            "parser_output": response.json()
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }