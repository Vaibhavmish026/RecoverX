import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CaseStatus

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.merchant import Merchant
    from app.models.recovery_action import RecoveryAction
    from app.models.transaction import Transaction


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, native_enum=False, length=50),
        default=CaseStatus.DETECTED,
        nullable=False,
        index=True,
    )
    diagnostic_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause_category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    selected_strategy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recovered_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

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
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="recovery_cases")
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="recovery_case")
    recovery_actions: Mapped[List["RecoveryAction"]] = relationship(
        "RecoveryAction",
        back_populates="recovery_case",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="recovery_case",
    )
