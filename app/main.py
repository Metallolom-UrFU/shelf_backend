from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import tasks
from .db_engine import get_db
from .db_models import Book
from .schemas import BookCreate, BookResponse

app = FastAPI()


@app.post("/test-task")
def test_task(name: str = "Test User"):
    """Trigger a test task"""
    tasks.example_task.send(name)
    return {"message": f"Task sent for {name}"}

@app.get("/")
def root():
    return {"message": "Hello World"}


@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(
    book_data: BookCreate,
    session: Session = Depends(get_db)
):
    """Create a new book"""
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


@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(
    book_id: UUID,
    session: Session = Depends(get_db)
):
    """Get a book by ID"""
    book = session.execute(
        select(Book).where(Book.id == book_id)
    ).scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(
    book_id: UUID,
    session: Session = Depends(get_db)
):
    """Delete a book by ID"""
    book = session.execute(
        select(Book).where(Book.id == book_id)
    ).scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    session.delete(book)
    session.commit()
    return None


