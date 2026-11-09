"""Shared, serialisable domain models."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Decision(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    UNCERTAIN = "uncertain"
    PENDING = "pending"


class CommentSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    EDITORIAL = "editorial"
    UNKNOWN = "unknown"


class CommentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ADDRESSED = "addressed"
    DEFERRED = "deferred"
    NOT_ADDRESSED = "not_addressed"


class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    abstract: str = ""
    doi: str | None = None
    journal: str | None = None
    source_database: str | None = None
    keywords: list[str] = Field(default_factory=list)
    url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ScreeningDecision(BaseModel):
    article_id: str
    stage: str = "title_abstract"
    decision: Decision = Decision.PENDING
    reasons: list[str] = Field(default_factory=list)
    reviewer: str | None = None
    notes: str = ""
    decided_at: datetime = Field(default_factory=utc_now)


class ReviewQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    question: str
    framework: str | None = None


class SupervisorComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_file: str
    source_format: str
    author: str | None = None
    date: str | None = None
    text: str
    anchor_text: str | None = None
    location: str | None = None
    context: str | None = None
    severity: CommentSeverity = CommentSeverity.UNKNOWN
    status: CommentStatus = CommentStatus.OPEN
    category: str = "unclassified"
    suggested_action: str = ""
    response: str = ""
    manuscript_location: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class JournalComment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    reviewer: str = "Reviewer"
    comment: str
    manuscript_location: str = ""
    response: str = ""
    action_taken: str = ""
    status: CommentStatus = CommentStatus.OPEN
    severity: CommentSeverity = CommentSeverity.UNKNOWN
    topic: str = "general"
    evidence_needed: list[str] = Field(default_factory=list)
