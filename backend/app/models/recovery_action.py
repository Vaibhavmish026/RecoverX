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
from app.models.enums import ActionStatus, ActionType

if TYPE_CHECKING:
    from app.models.recovery_case import RecoveryCase


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, native_enum=False, length=50),
        default=ActionStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    external_reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    action_payload: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    recovery_case: Mapped["RecoveryCase"] = relationship(
        "RecoveryCase",
        back_populates="recovery_actions",
    )
