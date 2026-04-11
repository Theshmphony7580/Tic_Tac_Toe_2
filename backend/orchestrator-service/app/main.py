from fastapi import FastAPI

app = FastAPI(title="Orchestrator")

@app.get("/")
async def root():
    return {"message": "Orchestrator running"}

@app.post("/process")
async def process_resume(data: dict):
    return {
        "status": "received",
        "file_url": data.get("file_url"),
        "file_type": data.get("file_type"),
        "message": "Processing started"
    }