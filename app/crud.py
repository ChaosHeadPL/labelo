from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.schemas import StorageCreate, StorageLabelCreate


async def create_storage_db(session: AsyncSession, data: StorageCreate) -> models.Storage:
    st = models.Storage(name=data.name, description=data.description)
    session.add(st)
    await session.commit()
    await session.refresh(st)
    return st

async def list_storages_db(session: AsyncSession):
    res = await session.execute(select(models.Storage).order_by(models.Storage.id))
    return list(res.scalars())

async def add_label_db(session: AsyncSession, storage_id: int, data: StorageLabelCreate) -> models.StorageLabel:
    st = await session.get(models.Storage, storage_id)
    if not st:
        raise ValueError("storage_not_found")
    label = models.StorageLabel(
        storage_id=storage_id,
        template_type=data.template_type,
        title=data.title,
        text=data.text,
        icon=data.icon,
        bg=data.bg,
        color=data.color,
        border=data.border,
        desired_qty=data.desired_qty,
        meta=data.meta,
    )
    session.add(label)
    await session.commit()
    await session.refresh(label)
    return label

async def list_labels_db(session: AsyncSession, storage_id: int):
    res = await session.execute(select(models.StorageLabel).where(models.StorageLabel.storage_id == storage_id).order_by(models.StorageLabel.id))
    return list(res.scalars())

async def mark_printed_db(session: AsyncSession, storage_id: int, label_id: int, qty: int):
    label = await session.get(models.StorageLabel, label_id)
    if not label or label.storage_id != storage_id:
        raise ValueError("label_not_found")
    label.printed_qty = max(0, (label.printed_qty or 0) + qty)
    await session.commit()
    await session.refresh(label)
    return label
