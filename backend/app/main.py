import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import engine, models, schemas
from .config import settings
from .database import get_db, init_db

app = FastAPI(title="The Forge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/api/health")
def health():
    return {"ok": True, "threshold": settings.readiness_threshold}


@app.get("/api/config")
def config():
    return {
        "readiness_threshold": settings.readiness_threshold,
        "statuses": models.STATUSES,
        "engine": "live" if settings.anthropic_api_key else "fallback",
    }


def _get_request(db: Session, request_id: int) -> models.Request:
    req = db.get(models.Request, request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    return req


@app.get("/api/requests", response_model=list[schemas.RequestOut])
def list_requests(db: Session = Depends(get_db)):
    return (
        db.query(models.Request)
        .order_by(models.Request.priority_score.desc().nullslast(),
                  models.Request.created_at.desc())
        .all()
    )


@app.post("/api/requests", response_model=schemas.RequestDetail)
def create_request(payload: schemas.RequestCreate, db: Session = Depends(get_db)):
    req = models.Request(
        title=payload.title,
        raw_idea=payload.raw_idea,
        created_by=payload.created_by,
        status="refining",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # Kick off the refine chat: engine asks its first gap-closing question.
    result = engine.run_engine(req, transcript=[])
    db.add(models.Message(request_id=req.id, role="engine", content=result["reply"]))
    req.readiness_score = result["readiness_score"]
    req.priority_score = result["priority_score"]
    db.commit()
    db.refresh(req)
    return req


@app.get("/api/requests/{request_id}", response_model=schemas.RequestDetail)
def get_request(request_id: int, db: Session = Depends(get_db)):
    return _get_request(db, request_id)


@app.post("/api/requests/{request_id}/refine", response_model=schemas.RefineOut)
def refine(request_id: int, payload: schemas.RefineIn, db: Session = Depends(get_db)):
    req = _get_request(db, request_id)

    # Record the requester's answer.
    db.add(models.Message(request_id=req.id, role="user", content=payload.content))
    db.commit()
    db.refresh(req)

    transcript = [(m.role, m.content) for m in req.messages]
    result = engine.run_engine(req, transcript)

    db.add(models.Message(request_id=req.id, role="engine", content=result["reply"]))
    req.readiness_score = result["readiness_score"]
    req.priority_score = result["priority_score"]
    if result["dev_prompt"]:
        req.dev_prompt = result["dev_prompt"]
    db.commit()
    db.refresh(req)

    at_threshold = req.readiness_score >= settings.readiness_threshold
    return schemas.RefineOut(
        reply=result["reply"],
        readiness_score=req.readiness_score,
        priority_score=req.priority_score,
        dev_prompt=req.dev_prompt,
        at_threshold=at_threshold,
    )


@app.post("/api/requests/{request_id}/status", response_model=schemas.RequestOut)
def set_status(request_id: int, payload: schemas.StatusUpdate, db: Session = Depends(get_db)):
    req = _get_request(db, request_id)
    if payload.status not in models.STATUSES:
        raise HTTPException(400, f"Invalid status. Use one of {models.STATUSES}")

    # The gate: cannot reach 'ready' until readiness clears the threshold.
    if payload.status == "ready" and (req.readiness_score or 0) < settings.readiness_threshold:
        raise HTTPException(
            409,
            f"Readiness {req.readiness_score or 0} is below the "
            f"{settings.readiness_threshold} threshold. Keep refining.",
        )
    req.status = payload.status
    db.commit()
    db.refresh(req)
    return req


@app.post("/api/requests/{request_id}/comments", response_model=schemas.RequestDetail)
def add_comment(request_id: int, payload: schemas.CommentCreate, db: Session = Depends(get_db)):
    req = _get_request(db, request_id)
    db.add(
        models.Comment(
            request_id=req.id,
            author=payload.author,
            body=payload.body,
            is_pushback=payload.is_pushback,
        )
    )
    # Pushback sends the card back to refining.
    if payload.is_pushback:
        req.status = "refining"
    db.commit()
    db.refresh(req)
    return req


# Single-service deploy: if the frontend has been built, serve it.
# `npm run build` in /frontend produces /frontend/dist. Mounted last so it
# never shadows the /api routes above.
_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="static")

