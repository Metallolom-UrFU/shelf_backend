from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db_engine import get_db
from ..db_models import Book, BookInstance, Shelf
from ..schemas import (
    BookCreate, BookResponse, BookInstanceResponse, BookInstanceCreate, BookInstanceStatus,
    BookUpdate, BookInstanceUpdate
)

router = APIRouter()

@router.get("/books", response_model=List[BookResponse])
def list_books(
        name: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        session: Session = Depends(get_db)
):
    """Поиск книг"""
    query = select(Book)
    if name:
        query = query.where(Book.name.ilike(f"%{name}%"))
    if author:
        query = query.where(Book.author.ilike(f"%{author}%"))
    if genre:
        query = query.where(Book.genre.ilike(f"%{genre}%"))
    return session.execute(query).scalars().all()


@router.post("/books", response_model=BookResponse, status_code=201)
def create_book(
        book_data: BookCreate,
        session: Session = Depends(get_db)
):
    """Создать новую книгу"""
    book = Book(
        name=book_data.name,
        author=book_data.author,
        description=book_data.description,
        cover_image_url=book_data.cover_image_url,
        genre=book_data.genre
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.get("/books/{book_id}", response_model=BookResponse)
def get_book(
        book_id: UUID,
        session: Session = Depends(get_db)
):
    """Получить книгу по ID"""
    book = session.execute(
        select(Book).where(Book.id == book_id)
    ).scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return book

@router.delete("/books/{book_id}", status_code=204)
def delete_book(
        book_id: UUID,
        session: Session = Depends(get_db)
):
    """Удалить книгу по ID"""
    book = session.execute(
        select(Book).where(Book.id == book_id)
    ).scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    session.delete(book)
    session.commit()
    return None


@router.put("/books/{book_id}", response_model=BookResponse)
def update_book(
        book_id: UUID,
        book_update: BookUpdate,
        session: Session = Depends(get_db)
):
    """Обновить информацию о книге"""
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    update_data = book_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)

    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.get("/books/{book_id}/instances", response_model=List[BookInstanceResponse])
def get_book_instances(book_id: UUID, session: Session = Depends(get_db)):
    """Получить доступные экземпляры книги"""
    return session.execute(
        select(BookInstance).where(
            BookInstance.book_id == book_id,
            BookInstance.status == BookInstanceStatus.AVAILABLE
        )
    ).scalars().all()


@router.post("/book-instances", response_model=BookInstanceResponse, status_code=201)
def create_book_instance(
        instance_data: BookInstanceCreate,
        session: Session = Depends(get_db)
):
    """Создать экземпляр книги (физический объект)"""
    book = session.get(Book, instance_data.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    shelf = session.get(Shelf, instance_data.shelf_id)
    if not shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    existing_instance = session.execute(
        select(BookInstance).where(BookInstance.book_code == instance_data.book_code)
    ).scalar_one_or_none()

    if existing_instance:
        raise HTTPException(status_code=400, detail="book code already registered")

    #todo: Проверять вместимость полки перед добавлением

    instance = BookInstance(
        book_id=instance_data.book_id,
        shelf_id=instance_data.shelf_id,
        shelf_pos=instance_data.shelf_pos,
        book_code=instance_data.book_code,
        status=instance_data.status
    )

    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


@router.delete("/book-instances/{instance_id}", status_code=204)
def delete_book_instance(instance_id: UUID, session: Session = Depends(get_db)):
    """Удалить экземпляр книги"""
    instance = session.get(BookInstance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Book instance not found")

    session.delete(instance)
    session.commit()
    return None


@router.put("/book-instances/{instance_id}", response_model=BookInstanceResponse)
def update_book_instance(
        instance_id: UUID,
        instance_update: BookInstanceUpdate,
        session: Session = Depends(get_db)
):
    """Обновить экземпляр книги"""
    instance = session.get(BookInstance, instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Book instance not found")

    update_data = instance_update.model_dump(exclude_unset=True)
    
    # Если обновляется book_code, проверяем уникальность
    if "book_code" in update_data and update_data["book_code"] != instance.book_code:
        existing = session.execute(
            select(BookInstance).where(BookInstance.book_code == update_data["book_code"])
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="book code already registered")

    for key, value in update_data.items():
        setattr(instance, key, value)

    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance
