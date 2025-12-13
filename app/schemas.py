from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ShelfStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class BookInstanceStatus(StrEnum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
    DAMAGED = "damaged"


class TransactionType(StrEnum):
    BORROW = "borrow"
    RETURN = "return"
    EXTEND = "extend"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class ReservationStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class UserRole(StrEnum):
    USER = "user"
    LIBRARIAN = "librarian"
    ADMIN = "admin"


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


class UserBase(BaseSchema):
    email: EmailStr
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ShelfBase(BaseSchema):
    name: str
    capacity: Decimal
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    status: ShelfStatus = ShelfStatus.ACTIVE


class ShelfCreate(ShelfBase):
    pass


class ShelfUpdate(BaseSchema):
    name: Optional[str] = None
    capacity: Optional[Decimal] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    status: Optional[ShelfStatus] = None


class ShelfResponse(ShelfBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class BookBase(BaseSchema):
    name: str
    author: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    genre: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseSchema):
    name: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    genre: Optional[str] = None


class BookResponse(BookBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class BookInstanceBase(BaseSchema):
    status: BookInstanceStatus = BookInstanceStatus.AVAILABLE
    shelf_pos: Decimal
    rfid_tag: str


class BookInstanceCreate(BookInstanceBase):
    book_id: UUID
    shelf_id: UUID


class BookInstanceUpdate(BaseSchema):
    status: Optional[BookInstanceStatus] = None
    shelf_pos: Optional[Decimal] = None
    rfid_tag: Optional[str] = None
    book_id: Optional[UUID] = None
    shelf_id: Optional[UUID] = None


class BookInstanceResponse(BookInstanceBase):
    id: UUID
    book_id: UUID
    shelf_id: UUID
    created_at: datetime
    updated_at: datetime


class TransactionBase(BaseSchema):
    type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING
    due_date: Optional[datetime] = None


class TransactionCreate(TransactionBase):
    user_id: UUID
    shelf_id: UUID
    book_instance_id: UUID


class TransactionUpdate(BaseSchema):
    status: Optional[TransactionStatus] = None
    due_date: Optional[datetime] = None
    type: Optional[TransactionType] = None


class TransactionResponse(TransactionBase):
    id: UUID
    date: datetime
    user_id: UUID
    shelf_id: UUID
    book_instance_id: UUID
    created_at: datetime
    updated_at: datetime


class ReservationBase(BaseSchema):
    status: ReservationStatus = ReservationStatus.PENDING
    exp_date: datetime


class ReservationCreate(ReservationBase):
    user_id: UUID
    book_instance_id: UUID


class ReservationUpdate(BaseSchema):
    status: Optional[ReservationStatus] = None
    exp_date: Optional[datetime] = None


class ReservationResponse(ReservationBase):
    id: UUID
    date: datetime
    user_id: UUID
    book_instance_id: UUID
    pickup_code: Optional[str] = None
    qr_code_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
