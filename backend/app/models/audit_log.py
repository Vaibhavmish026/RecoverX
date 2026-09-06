import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActorType

if TYPE_CHECKING:
    from app.models.recovery_case import RecoveryCase


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    event_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    state_before: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    state_after: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    agent_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    recovery_case: Mapped[Optional["RecoveryCase"]] = relationship(
        "RecoveryCase",
        back_populates="audit_logs",
    )
