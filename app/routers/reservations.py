from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db_engine import get_db
from ..db_models import Reservation, BookInstance
from ..schemas import ReservationCreate, ReservationResponse, ReservationStatus, BookInstanceStatus, ReservationUpdate

router = APIRouter()

@router.post("/reservations", response_model=ReservationResponse)
def create_reservation(
        reservation_data: ReservationCreate,
        session: Session = Depends(get_db)
):
    """Зарезервировать экземпляр книги"""
    instance = session.get(BookInstance, reservation_data.book_instance_id)
    if not instance:
        raise HTTPException(404, "Book instance not found")
    if instance.status != BookInstanceStatus.AVAILABLE:
        raise HTTPException(400, "Book instance not available")

    reservation = Reservation(
        user_id=reservation_data.user_id,
        book_instance_id=reservation_data.book_instance_id,
        exp_date=reservation_data.exp_date,
        status=ReservationStatus.PENDING
    )

    instance.status = BookInstanceStatus.RESERVED

    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation


@router.get("/users/{user_id}/reservations", response_model=List[ReservationResponse])
def list_user_reservations(user_id: UUID, session: Session = Depends(get_db)):
    """Список активных бронирований пользователя"""
    return session.execute(
        select(Reservation).where(
            Reservation.user_id == user_id,
            Reservation.status == ReservationStatus.PENDING
        )
    ).scalars().all()


@router.delete("/reservations/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: UUID, session: Session = Depends(get_db)):
    """Удалить бронирование"""
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.status == ReservationStatus.PENDING:
        instance = session.get(BookInstance, reservation.book_instance_id)
        if instance and instance.status == BookInstanceStatus.RESERVED:
            instance.status = BookInstanceStatus.AVAILABLE

    session.delete(reservation)
    session.commit()
    return None


@router.put("/reservations/{reservation_id}", response_model=ReservationResponse)
def update_reservation(
        reservation_id: UUID,
        reservation_update: ReservationUpdate,
        session: Session = Depends(get_db)
):
    """Обновить бронирование"""
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    update_data = reservation_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reservation, key, value)

    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation
