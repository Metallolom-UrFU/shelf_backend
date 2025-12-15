from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db_engine import get_db
from ..db_models import Shelf, BookInstance
from ..schemas import ShelfCreate, ShelfResponse, ShelfUpdate, BookInstanceResponse

router = APIRouter()

@router.get("/shelves", response_model=List[ShelfResponse])
def list_shelves(session: Session = Depends(get_db)):
    """Список всех полок (стендов)"""
    return session.execute(select(Shelf)).scalars().all()


@router.post("/shelves", response_model=ShelfResponse, status_code=201)
def create_shelf(
        shelf_data: ShelfCreate,
        session: Session = Depends(get_db)
):
    """Создать новую полку (стенд)"""
    # todo: Проверять имя на уникальность?

    shelf = Shelf(
        name=shelf_data.name,
        capacity=shelf_data.capacity,
        latitude=shelf_data.latitude,
        longitude=shelf_data.longitude,
        status=shelf_data.status
    )
    session.add(shelf)
    session.commit()
    session.refresh(shelf)
    return shelf


@router.get("/shelves/{shelf_id}", response_model=ShelfResponse)
def get_shelf(shelf_id: UUID, session: Session = Depends(get_db)):
    """Получить информацию о полке"""
    shelf = session.get(Shelf, shelf_id)
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")
    return shelf


@router.delete("/shelves/{shelf_id}", status_code=204)
def delete_shelf(shelf_id: UUID, session: Session = Depends(get_db)):
    """Удалить полку"""
    shelf = session.get(Shelf, shelf_id)
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    session.delete(shelf)
    session.commit()
    return None


@router.put("/shelves/{shelf_id}", response_model=ShelfResponse)
def update_shelf(
        shelf_id: UUID,
        shelf_update: ShelfUpdate,
        session: Session = Depends(get_db)
):
    """Обновить информацию о полке"""
    shelf = session.get(Shelf, shelf_id)
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    update_data = shelf_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(shelf, key, value)

    session.add(shelf)
    session.commit()
    session.refresh(shelf)
    return shelf


@router.get("/shelves/{shelf_id}/books", response_model=List[BookInstanceResponse])
def list_shelf_books(shelf_id: UUID, session: Session = Depends(get_db)):
    """Список книг на полке"""
    shelf = session.get(Shelf, shelf_id)
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")
    
    return session.execute(
        select(BookInstance).where(BookInstance.shelf_id == shelf_id)
    ).scalars().all()
