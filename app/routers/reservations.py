from typing import List
from uuid import UUID
import secrets
import string
from datetime import datetime, UTC
import io

import boto3
import qrcode
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from botocore.config import Config

from ..db_engine import get_db
from ..db_models import Reservation, BookInstance, Transaction
from ..schemas import ReservationCreate, ReservationResponse, ReservationStatus, BookInstanceStatus, ReservationUpdate, \
    TransactionStatus, TransactionType, TransactionResponse, ReservationWithBooksResponse
from ..settings import Settings

router = APIRouter()
settings = Settings()


def generate_and_upload_qr(pickup_code: str, reservation_id: UUID) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(pickup_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    s3_client = boto3.client(
        's3',
        endpoint_url=settings.s3.endpoint_url,
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
        region_name=settings.s3.region_name,
        config=Config(signature_version='s3v4')
    )

    file_path = f"orders/{reservation_id}.png"
    s3_client.upload_fileobj(
        img_byte_arr,
        settings.s3.bucket_name,
        file_path,
        ExtraArgs={'ContentType': 'image/png'}
    )

    return f"{settings.s3.endpoint_url}/{settings.s3.bucket_name}/{file_path}"


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

    pickup_code = ''.join(secrets.choice(string.digits) for _ in range(6))

    reservation = Reservation(
        user_id=reservation_data.user_id,
        book_instance_id=reservation_data.book_instance_id,
        exp_date=reservation_data.exp_date,
        status=ReservationStatus.PENDING,
        pickup_code=pickup_code
    )

    instance.status = BookInstanceStatus.RESERVED

    session.add(reservation)
    session.commit()
    session.refresh(reservation)

    try:
        qr_url = generate_and_upload_qr(pickup_code, reservation.id)
        reservation.qr_code_url = qr_url
        session.commit()
        session.refresh(reservation)
    except Exception as e:
        print(f"Failed to generate/upload QR code: {e}")

    return reservation


@router.get("/users/{user_id}/reservations", response_model=List[ReservationWithBooksResponse])
def list_user_reservations(user_id: UUID, session: Session = Depends(get_db)):
    """Список активных бронирований пользователя"""
    reservations = session.execute(
        select(Reservation)
        .options(joinedload(Reservation.book_instance).joinedload(BookInstance.book))
        .where(
            Reservation.user_id == user_id,
            Reservation.status == ReservationStatus.PENDING
        )
    ).scalars().all()

    response = []
    for res in reservations:
        response.append(ReservationWithBooksResponse(
            **res.__dict__,
            book=res.book_instance.book
        ))
    return response


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


@router.post("/reservations/pickup", response_model=TransactionResponse)
def pickup_reservation(
        pickup_code: str,
        session: Session = Depends(get_db)
):
    """Получить книгу по коду бронирования"""
    reservation = session.execute(
        select(Reservation).where(
            Reservation.pickup_code == pickup_code,
            Reservation.status == ReservationStatus.PENDING
        )
    ).scalars().first()

    if not reservation:
        raise HTTPException(404, "Invalid or expired pickup code")

    if reservation.exp_date.replace(tzinfo=UTC) < datetime.now(UTC):
        reservation.status = ReservationStatus.EXPIRED
        session.commit()
        raise HTTPException(400, "Reservation expired")

    instance = session.get(BookInstance, reservation.book_instance_id)
    if not instance:
        raise HTTPException(404, "Book instance not found")

    transaction = Transaction(
        user_id=reservation.user_id,
        book_instance_id=reservation.book_instance_id,
        shelf_id=instance.shelf_id,
        type=TransactionType.BORROW,
        status=TransactionStatus.PENDING,  #todo: Тут может completed статус
        date=datetime.now(UTC)
    )

    reservation.status = ReservationStatus.COMPLETED

    instance.status = BookInstanceStatus.BORROWED

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return transaction
