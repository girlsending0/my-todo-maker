from __future__ import annotations

from datetime import date

import aiosqlite

from app.models import TodoCreate, TodoUpdate


async def create_todo(db: aiosqlite.Connection, todo: TodoCreate) -> dict:
    due_time_str = todo.due_time.isoformat() if todo.due_time else None
    cursor = await db.execute(
        "INSERT INTO todos (title, due_date, due_time) VALUES (?, ?, ?)",
        (todo.title, todo.due_date.isoformat(), due_time_str),
    )
    await db.commit()
    row = await db.execute_fetchall(
        "SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)
    )
    return dict(row[0])


async def get_todos_by_date(db: aiosqlite.Connection, target_date: date) -> list[dict]:
    rows = await db.execute_fetchall(
        "SELECT * FROM todos WHERE due_date = ? ORDER BY due_time ASC, id ASC",
        (target_date.isoformat(),),
    )
    return [dict(r) for r in rows]


async def get_todos_by_date_range(
    db: aiosqlite.Connection, start: date, end: date
) -> list[dict]:
    rows = await db.execute_fetchall(
        "SELECT * FROM todos WHERE due_date BETWEEN ? AND ? ORDER BY due_date, due_time ASC, id ASC",
        (start.isoformat(), end.isoformat()),
    )
    return [dict(r) for r in rows]


async def update_todo(db: aiosqlite.Connection, todo_id: int, update: TodoUpdate) -> dict | None:
    fields = []
    values = []
    if update.title is not None:
        fields.append("title = ?")
        values.append(update.title)
    if update.is_completed is not None:
        fields.append("is_completed = ?")
        values.append(int(update.is_completed))

    if not fields:
        return None

    values.append(todo_id)
    await db.execute(
        f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", values
    )
    await db.commit()
    rows = await db.execute_fetchall("SELECT * FROM todos WHERE id = ?", (todo_id,))
    return dict(rows[0]) if rows else None


async def delete_todo(db: aiosqlite.Connection, todo_id: int) -> bool:
    cursor = await db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    await db.commit()
    return cursor.rowcount > 0


async def get_incomplete_todos_for_date(db: aiosqlite.Connection, target_date: date) -> list[dict]:
    rows = await db.execute_fetchall(
        "SELECT * FROM todos WHERE due_date = ? AND is_completed = 0 ORDER BY due_time ASC, id ASC",
        (target_date.isoformat(),),
    )
    return [dict(r) for r in rows]
