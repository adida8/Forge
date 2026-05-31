from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def _now():
    return datetime.now(timezone.utc)


# Board columns. A request moves left-to-right through these.
STATUSES = ["refining", "ready", "in_review", "building", "done"]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # requester | developer


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    raw_idea = Column(Text, nullable=False)
    status = Column(String, default="refining", nullable=False)
    priority_score = Column(Integer, nullable=True)
    readiness_score = Column(Integer, nullable=True)
    dev_prompt = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    messages = relationship(
        "Message",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    comments = relationship(
        "Comment",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )


class Message(Base):
    """One turn of the refine-chat transcript."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    role = Column(String, nullable=False)  # user | engine
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now)

    request = relationship("Request", back_populates="messages")


class Comment(Base):
    """Developer review thread on a request."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    author = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_pushback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)

    request = relationship("Request", back_populates="comments")
