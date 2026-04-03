import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import init_db, SessionLocal, ErrorLog
from app.summarizer import summarize_error
from app.email_service import send_alert_email
from dotenv import load_dotenv

load_dotenv(".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="PocketCMO Monitor", lifespan=lifespan)

# Setup templates and static (we will create templates folder next)
# Using generic paths but will run from the root of pocketcmo-monitor
templates = Jinja2Templates(directory="app/templates")

class LogIngestRequest(BaseModel):
    service_name: str
    level: str
    message: str
    raw_error: str = ""

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def process_and_alert(data: LogIngestRequest, db: Session):
    """Background task to summarize error and optionally alert."""
    # 1. Summarize
    ai_summary = summarize_error(data.service_name, data.message, data.raw_error)
    
    # 2. Save to DB
    new_log = ErrorLog(
        service_name=data.service_name,
        level=data.level,
        message=data.message,
        raw_error=data.raw_error,
        ai_summary=ai_summary
    )
    db.add(new_log)
    db.commit()
    
    # 3. Send Alert if Critical or Error (and not a test string)
    if data.level in ["ERROR", "CRITICAL"]:
        send_alert_email(data.service_name, data.level, data.message, ai_summary)

@app.post("/api/logs/ingest")
async def ingest_log(data: LogIngestRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Webhook endpoint for PocketCMO Backend to push errors."""
    background_tasks.add_task(process_and_alert, data, db)
    return {"status": "ingesting", "message": "Log received and processing in background"}

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    """Render the dashboard UI."""
    logs = db.query(ErrorLog).order_by(ErrorLog.timestamp.desc()).limit(50).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "logs": logs})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
