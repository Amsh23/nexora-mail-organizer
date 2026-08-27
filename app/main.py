import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import repository
from database import initialize_database
from sync_service import run_sync

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Nexora Mail")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup():
    initialize_database()


@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, **repository.dashboard_stats()})


@app.get("/emails")
def emails(request: Request, q: str = "", category: str = "", page: int = 1, sort: str = "received_at", direction: str = "desc"):
    rows, total = repository.list_emails(q, category, max(page, 1), sort=sort, direction=direction)
    return templates.TemplateResponse("emails.html", {"request": request, "emails": rows, "total": total, "page": page, "q": q, "category": category, "categories": repository.categories(), "sort": sort, "direction": direction})


@app.get("/emails/{email_id}")
def email_detail(request: Request, email_id: int):
    email = repository.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return templates.TemplateResponse("email_detail.html", {"request": request, "email": email, "attachments": repository.email_attachments(email_id)})


@app.get("/attachments")
def attachments(request: Request, category: str = "", filename: str = "", extension: str = ""):
    return templates.TemplateResponse("attachments.html", {"request": request, "attachments": repository.list_attachments(category, filename, extension), "categories": repository.categories(), "category": category, "filename": filename, "extension": extension})


@app.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int):
    path = repository.attachment_download_path(attachment_id)
    if not path:
        raise HTTPException(status_code=404, detail="Attachment file not found")
    return FileResponse(path, filename=path.name)


@app.get("/statistics")
def statistics(request: Request):
    return templates.TemplateResponse("statistics.html", {"request": request, **repository.dashboard_stats()})


@app.get("/search")
def search(request: Request, q: str = Query("", max_length=200)):
    return templates.TemplateResponse("search.html", {"request": request, "q": q, "results": repository.search_emails(q)})


def background_sync():
    try:
        run_sync(dry_run=False)
    except Exception:
        logger.exception("Background Gmail sync failed")


@app.post("/sync")
def sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(background_sync)
    return RedirectResponse("/?sync=started", status_code=303)
