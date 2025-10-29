import uuid
from datetime import datetime, UTC
from decimal import Decimal

import sqlalchemy
from sqlalchemy import orm, ForeignKey, Enum
from sqlalchemy.dialects import postgresql
from schemas import UserRole, ShelfStatus, BookInstanceStatus, TransactionStatus, TransactionType, ReservationStatus


class DeclarativeBase(orm.DeclarativeBase):
    """база"""


class Base(DeclarativeBase):
    __abstract__ = True

    created_at: orm.Mapped[datetime] = orm.mapped_column(sqlalchemy.DateTime, default=datetime.now(UTC))
    updated_at: orm.Mapped[datetime] = orm.mapped_column(sqlalchemy.DateTime, default=datetime.now(UTC),
                                                         onupdate=datetime.now(UTC))


class BaseWithPK(Base):
    __abstract__ = True

    id: orm.Mapped[uuid.UUID] = orm.mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# Models
class User(BaseWithPK):
    __tablename__ = "user"

    email: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, unique=True, nullable=False)
    password_hash: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=False)
    is_active: orm.Mapped[bool] = orm.mapped_column(sqlalchemy.Boolean, default=True)
    role: orm.Mapped[UserRole] = orm.mapped_column(Enum(UserRole), default=UserRole.USER)

    # Relationships
    reservations: orm.Mapped[list["Reservation"]] = orm.relationship(back_populates="user")


class Shelf(BaseWithPK):
    __tablename__ = "shelve"

    name: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=False)
    capacity: orm.Mapped[Decimal] = orm.mapped_column(sqlalchemy.Numeric(10, 2), nullable=False)
    latitude: orm.Mapped[Decimal] = orm.mapped_column(sqlalchemy.Numeric(10, 8), nullable=True)
    longitude: orm.Mapped[Decimal] = orm.mapped_column(sqlalchemy.Numeric(11, 8), nullable=True)
    status: orm.Mapped[ShelfStatus] = orm.mapped_column(Enum(ShelfStatus), default=ShelfStatus.ACTIVE)

    # Relationships
    book_instances: orm.Mapped[list["BookInstance"]] = orm.relationship(back_populates="shelf")
    transactions: orm.Mapped[list["Transaction"]] = orm.relationship(back_populates="shelf")


class Book(BaseWithPK):
    __tablename__ = "book"

    name: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=False)
    author: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=False)
    description: orm.Mapped[str] = orm.mapped_column(sqlalchemy.Text, nullable=True)
    cover_image_url: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=True)
    genre: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, nullable=True)

    # Relationships
    book_instances: orm.Mapped[list["BookInstance"]] = orm.relationship(back_populates="book")


class BookInstance(BaseWithPK):
    __tablename__ = "book_instance"

    status: orm.Mapped[BookInstanceStatus] = orm.mapped_column(Enum(BookInstanceStatus), default=BookInstanceStatus.AVAILABLE)
    shelf_pos: orm.Mapped[Decimal] = orm.mapped_column(sqlalchemy.Numeric(10, 2), nullable=False)
    rfid_tag: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String, unique=True, nullable=False)
    
    # Foreign Keys
    book_id: orm.Mapped[uuid.UUID] = orm.mapped_column(ForeignKey("book.id"), nullable=False)
    shelf_id: orm.Mapped[uuid.UUID] = orm.mapped_column(ForeignKey("shelve.id"), nullable=False)

    # Relationships
    book: orm.Mapped["Book"] = orm.relationship(back_populates="book_instances")
    shelf: orm.Mapped["Shelf"] = orm.relationship(back_populates="book_instances")
    transactions: orm.Mapped[list["Transaction"]] = orm.relationship(back_populates="book_instance")
    reservations: orm.Mapped[list["Reservation"]] = orm.relationship(back_populates="book_instance")


class Transaction(BaseWithPK):
    __tablename__ = "transaction"

    date: orm.Mapped[datetime] = orm.mapped_column(sqlalchemy.DateTime, default=datetime.now(UTC))
    status: orm.Mapped[TransactionStatus] = orm.mapped_column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    due_date: orm.Mapped[datetime] = orm.mapped_column(sqlalchemy.DateTime, nullable=True)
    type: orm.Mapped[TransactionType] = orm.mapped_column(Enum(TransactionType), nullable=False)
    
    # Foreign Keys
    shelf_id: orm.Mapped[uuid.UUID] = orm.mapped_column(ForeignKey("shelve.id"), nullable=False)
    book_instance_id: orm.Mapped[uuid.UUID] = orm.mapped_column(ForeignKey("book_instance.id"), nullable=False)

    # Relationships
    shelf: orm.Mapped["Shelf"] = orm.relationship(back_populates="transactions")
    book_instance: orm.Mapped["BookInstance"] = orm.relationship(back_populates="transactions")


class Reservation(BaseWithPK):
    __tablename__ = "reservation"

    status: orm.Mapped[ReservationStatus] = orm.mapped_column(Enum(ReservationStatus), default=ReservationStatus.PENDING)
    date: orm.Mapped[datetime] = orm.mapped_column(sqlalchemy.DateTime, default=datetime.now(UTC))
    exp_date: orm.Mapped[datetime] = orm.mapped_column(sqlalchemy.DateTime, nullable=False)
    
    # Foreign Keys
    user_id: orm.Mapped[uuid.UUID] = orm.mapped_column(ForeignKey("user.id"), nullable=False)
    book_instance_id: orm.Mapped[uuid.UUID] = orm.mapped_column(ForeignKey("book_instance.id"), nullable=False)

    # Relationships
    user: orm.Mapped["User"] = orm.relationship(back_populates="reservations")
    book_instance: orm.Mapped["BookInstance"] = orm.relationship(back_populates="reservations")
