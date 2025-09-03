from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.db import Base


class Storage(Base):
    __tablename__ = "storages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())
    labels: Mapped[list[StorageLabel]] = relationship("StorageLabel", back_populates="storage", cascade="all, delete-orphan")

class StorageLabel(Base):
    __tablename__ = "storage_labels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    storage_id: Mapped[int] = mapped_column(ForeignKey("storages.id", ondelete="CASCADE"))
    template_type: Mapped[str] = mapped_column(String(64), default="jar_label_small")
    title: Mapped[str] = mapped_column(String(200))
    text: Mapped[str | None] = mapped_column(String(500))
    icon: Mapped[str | None] = mapped_column(String(120))
    bg: Mapped[str | None] = mapped_column(String(16))
    color: Mapped[str | None] = mapped_column(String(16))
    border: Mapped[str | None] = mapped_column(String(16))
    meta: Mapped[dict | None] = mapped_column(JSON)
    desired_qty: Mapped[int] = mapped_column(Integer, default=0)
    printed_qty: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

    storage: Mapped[Storage] = relationship("Storage", back_populates="labels")

    @property
    def missing_qty(self) -> int:
        d = self.desired_qty or 0
        p = self.printed_qty or 0
        return max(d - p, 0)
