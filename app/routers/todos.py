from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Response

from app.database import get_db
from app.models import TodoCreate, TodoUpdate
from app.crud import (
    create_todo,
    get_todos_by_date,
    get_todos_by_date_range,
    update_todo,
    delete_todo,
)

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.post("", status_code=201)
async def create(todo: TodoCreate):
    db = await get_db()
    try:
        result = await create_todo(db, todo)
        return result
    finally:
        await db.close()


@router.get("")
async def list_todos(
    date_param: Optional[date] = Query(None, alias="date"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
):
    db = await get_db()
    try:
        if date_param:
            return await get_todos_by_date(db, date_param)
        elif start and end:
            return await get_todos_by_date_range(db, start, end)
        return await get_todos_by_date(db, date.today())
    finally:
        await db.close()


@router.patch("/{todo_id}")
async def update(todo_id: int, body: TodoUpdate):
    db = await get_db()
    try:
        result = await update_todo(db, todo_id, body)
        if result is None:
            return Response(status_code=404)
        return result
    finally:
        await db.close()


@router.delete("/{todo_id}", status_code=204)
async def delete(todo_id: int):
    db = await get_db()
    try:
        success = await delete_todo(db, todo_id)
        if not success:
            return Response(status_code=404)
        return Response(status_code=204)
    finally:
        await db.close()
