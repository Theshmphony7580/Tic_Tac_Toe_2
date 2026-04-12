import httpx
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

app = FastAPI()

PARSER_URL = os.getenv("PARSER_URL")
NORMALIZATION_URL = os.getenv("NORMALIZATION_URL")


@app.post("/process")
async def process_resume(data: dict):

    file_path = data.get("file_url")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:

            # STEP 1: Parser
            with open(file_path, "rb") as f:
                files = {
                    "file": (os.path.basename(file_path), f)
                }

                parser_res = await client.post(PARSER_URL, files=files)

            parsed_data = parser_res.json()

            # Check parser success
            if not parsed_data.get("success"):
                return {
                    "status": "failed",
                    "stage": "parser",
                    "error": parsed_data
                }

            # STEP 2: Prepare input for normalizer
            normalization_input = {
                "raw_skills": parsed_data.get("data", {}).get("raw_skills", [])
            }

            # STEP 3: Call normalizer
            norm_res = await client.post(
                NORMALIZATION_URL,
                json=normalization_input
            )

            normalized_data = norm_res.json()

        # FINAL RESPONSE
        return {
            "status": "success",
            "parsed": parsed_data,
            "normalized": normalized_data
        }

    except httpx.ConnectError:
        return {
            "status": "failed",
            "error": "Service not reachable"
        }

    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR TRACE:\n", tb)

        return {
            "status": "failed",
            "error": str(e),
            "trace": tb
        }