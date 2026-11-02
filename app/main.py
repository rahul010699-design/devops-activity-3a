
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Integer, String, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./inventory.db",
)

connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    quantity: Mapped[int] = mapped_column(Integer, default=0)


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    quantity: int = Field(default=0, ge=0)


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    quantity: int | None = Field(default=None, ge=0)


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    quantity: int


def get_db():
    with SessionLocal() as db:
        yield db


DatabaseSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Secure Inventory API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(payload: ItemCreate, db: DatabaseSession):
    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/items", response_model=list[ItemResponse])
def list_items(db: DatabaseSession):
    return db.scalars(select(Item).order_by(Item.id)).all()


@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: DatabaseSession):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: DatabaseSession,
):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: DatabaseSession):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
