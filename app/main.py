from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Body
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from . import tasks
from .db_engine import get_db
from .db_models import BookInstance, Transaction, Reservation
from .schemas import (
    TransactionResponse, BookInstanceStatus, TransactionType,
    TransactionStatus, ReservationStatus
)
from .routers import books, shelves, reservations

app = FastAPI()

app.include_router(books.router, tags=["Books"])
app.include_router(shelves.router, tags=["Shelves"])
app.include_router(reservations.router, tags=["Reservations"])


@app.post("/test-task")
def test_task(name: str = "Test User"):
    """Запустить тестовую задачу"""
    tasks.example_task.send(name)
    return {"message": f"Task sent for {name}"}


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/borrow", response_model=TransactionResponse)
def borrow_book(
        user_id: UUID = Body(...),
        rfid_tag: str = Body(...),
        session: Session = Depends(get_db)
):
    """Взять книгу"""
    instance = session.execute(
        select(BookInstance).where(BookInstance.rfid_tag == rfid_tag)
    ).scalar_one_or_none()

    if not instance:
        raise HTTPException(404, "Book instance not found")

    if instance.status not in [BookInstanceStatus.AVAILABLE, BookInstanceStatus.RESERVED]:
        raise HTTPException(400, "Book is not available")

    if instance.status == BookInstanceStatus.RESERVED:
        res = session.execute(
            select(Reservation).where(
                Reservation.book_instance_id == instance.id,
                Reservation.status == ReservationStatus.PENDING,
                Reservation.user_id == user_id
            )
        ).scalar_one_or_none()
        if not res:
            raise HTTPException(400, "Book is reserved by another user")
        res.status = ReservationStatus.COMPLETED

    transaction = Transaction(
        user_id=user_id,
        shelf_id=instance.shelf_id,
        book_instance_id=instance.id,
        type=TransactionType.BORROW,
        status=TransactionStatus.PENDING
    )

    instance.status = BookInstanceStatus.BORROWED

    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


@app.post("/return", response_model=TransactionResponse)
def return_book(
        rfid_tag: str = Body(...),
        shelf_id: UUID = Body(...),
        session: Session = Depends(get_db)
):
    """Вернуть книгу"""
    instance = session.execute(
        select(BookInstance).where(BookInstance.rfid_tag == rfid_tag)
    ).scalar_one_or_none()

    if not instance:
        raise HTTPException(404, "Book instance not found")

    last_borrow = session.execute(
        select(Transaction).where(
            Transaction.book_instance_id == instance.id,
            Transaction.type == TransactionType.BORROW,
            Transaction.status == TransactionStatus.PENDING
        ).order_by(desc(Transaction.date))
    ).scalar_one_or_none()

    if not last_borrow:
        raise HTTPException(400, "Book was not borrowed")

    last_borrow.status = TransactionStatus.COMPLETED

    return_tx = Transaction(
        user_id=last_borrow.user_id,
        shelf_id=shelf_id,
        book_instance_id=instance.id,
        type=TransactionType.RETURN,
        status=TransactionStatus.COMPLETED
    )

    instance.status = BookInstanceStatus.AVAILABLE
    instance.shelf_id = shelf_id

    session.add(return_tx)
    session.commit()
    session.refresh(return_tx)
    return return_tx


@app.post("/return-quick", response_model=TransactionResponse)
def return_book_quick(
        rfid_tag: str = Body(..., embed=True),
        session: Session = Depends(get_db)
):
    """Вернуть книгу без указания полки"""
    instance = session.execute(
        select(BookInstance).where(BookInstance.rfid_tag == rfid_tag)
    ).scalar_one_or_none()

    if not instance:
        raise HTTPException(404, "Book instance not found")

    last_borrow = session.execute(
        select(Transaction).where(
            Transaction.book_instance_id == instance.id,
            Transaction.type == TransactionType.BORROW,
            Transaction.status == TransactionStatus.PENDING
        ).order_by(desc(Transaction.date))
    ).scalar_one_or_none()

    if not last_borrow:
        raise HTTPException(400, "Book was not borrowed")

    last_borrow.status = TransactionStatus.COMPLETED

    # Используем текущую полку книги (откуда взяли)
    return_tx = Transaction(
        user_id=last_borrow.user_id,
        shelf_id=instance.shelf_id,
        book_instance_id=instance.id,
        type=TransactionType.RETURN,
        status=TransactionStatus.COMPLETED
    )

    instance.status = BookInstanceStatus.AVAILABLE
    # instance.shelf_id не меняем, так как возвращаем туда же

    session.add(return_tx)
    session.commit()
    session.refresh(return_tx)
    return return_tx


@app.get("/users/{user_id}/history", response_model=List[TransactionResponse])
def user_history(user_id: UUID, session: Session = Depends(get_db)):
    """Получить историю операций пользователя"""
    return session.execute(
        select(Transaction).where(Transaction.user_id == user_id).order_by(desc(Transaction.date))
    ).scalars().all()


@app.get("/admin/transactions", response_model=List[TransactionResponse])
def admin_transactions(session: Session = Depends(get_db)):
    """Панель администратора: просмотр всех транзакций"""
    return session.execute(
        select(Transaction).order_by(desc(Transaction.date)).limit(100)
    ).scalars().all()

