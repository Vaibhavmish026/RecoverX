import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.transaction import Transaction
    from app.models.recovery_case import RecoveryCase


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    razorpay_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

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
    customers: Mapped[List["Customer"]] = relationship(
        "Customer",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
    recovery_cases: Mapped[List["RecoveryCase"]] = relationship(
        "RecoveryCase",
        back_populates="merchant",
        cascade="all, delete-orphan",
    )
