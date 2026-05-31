from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---- Request ----
class RequestCreate(BaseModel):
    title: str
    raw_idea: str
    created_by: Optional[str] = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    created_at: datetime


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author: str
    body: str
    is_pushback: bool
    created_at: datetime


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    raw_idea: str
    status: str
    priority_score: Optional[int]
    readiness_score: Optional[int]
    dev_prompt: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class RequestDetail(RequestOut):
    messages: list[MessageOut] = []
    comments: list[CommentOut] = []


# ---- Refine chat ----
class RefineIn(BaseModel):
    content: str  # the requester's answer to the engine's question


class RefineOut(BaseModel):
    reply: str
    readiness_score: int
    priority_score: int
    dev_prompt: Optional[str] = None
    at_threshold: bool


# ---- Comments / status ----
class CommentCreate(BaseModel):
    author: str
    body: str
    is_pushback: bool = False


class StatusUpdate(BaseModel):
    status: str
