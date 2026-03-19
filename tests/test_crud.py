import pytest
import pytest_asyncio
import aiosqlite
from datetime import date, time

from app.crud import create_todo, get_todos_by_date, update_todo, delete_todo, get_incomplete_todos_for_date
from app.database import init_db
from app.models import TodoCreate, TodoUpdate


@pytest_asyncio.fixture
async def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    await init_db(db_path)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_create_todo(db):
    todo = TodoCreate(title="병원 가기", due_date=date(2026, 3, 19), due_time=time(15, 0))
    result = await create_todo(db, todo)

    assert result["id"] == 1
    assert result["title"] == "병원 가기"
    assert result["due_date"] == "2026-03-19"
    assert result["due_time"] == "15:00:00"
    assert result["is_completed"] == 0


@pytest.mark.asyncio
async def test_create_todo_without_time(db):
    todo = TodoCreate(title="빨래하기", due_date=date(2026, 3, 19))
    result = await create_todo(db, todo)

    assert result["title"] == "빨래하기"
    assert result["due_time"] is None


@pytest.mark.asyncio
async def test_get_todos_by_date(db):
    await create_todo(db, TodoCreate(title="할일1", due_date=date(2026, 3, 19)))
    await create_todo(db, TodoCreate(title="할일2", due_date=date(2026, 3, 19)))
    await create_todo(db, TodoCreate(title="다른날", due_date=date(2026, 3, 20)))

    todos = await get_todos_by_date(db, date(2026, 3, 19))
    assert len(todos) == 2
    assert todos[0]["title"] == "할일1"


@pytest.mark.asyncio
async def test_update_todo_complete(db):
    await create_todo(db, TodoCreate(title="운동", due_date=date(2026, 3, 19)))
    result = await update_todo(db, 1, TodoUpdate(is_completed=True))

    assert result["is_completed"] == 1


@pytest.mark.asyncio
async def test_update_todo_title(db):
    await create_todo(db, TodoCreate(title="운동", due_date=date(2026, 3, 19)))
    result = await update_todo(db, 1, TodoUpdate(title="헬스장 가기"))

    assert result["title"] == "헬스장 가기"


@pytest.mark.asyncio
async def test_delete_todo(db):
    await create_todo(db, TodoCreate(title="삭제할것", due_date=date(2026, 3, 19)))
    success = await delete_todo(db, 1)
    assert success is True

    todos = await get_todos_by_date(db, date(2026, 3, 19))
    assert len(todos) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_todo(db):
    success = await delete_todo(db, 999)
    assert success is False


@pytest.mark.asyncio
async def test_get_incomplete_todos(db):
    await create_todo(db, TodoCreate(title="완료한것", due_date=date(2026, 3, 19)))
    await create_todo(db, TodoCreate(title="안한것", due_date=date(2026, 3, 19)))
    await update_todo(db, 1, TodoUpdate(is_completed=True))

    incomplete = await get_incomplete_todos_for_date(db, date(2026, 3, 19))
    assert len(incomplete) == 1
    assert incomplete[0]["title"] == "안한것"
