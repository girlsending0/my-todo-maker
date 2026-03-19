import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    import app.database as db_mod
    import app.routers.todos as router_mod
    test_db = str(tmp_path / "test.db")
    db_mod.DB_PATH = test_db
    await init_db(test_db)


@pytest.mark.anyio
async def test_create_todo():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/todos", json={
            "title": "테스트 할일",
            "due_date": "2026-03-19",
            "due_time": "15:00:00",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "테스트 할일"
        assert data["due_date"] == "2026-03-19"


@pytest.mark.anyio
async def test_get_todos_by_date():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/todos", json={"title": "할일A", "due_date": "2026-03-20"})
        await client.post("/api/todos", json={"title": "할일B", "due_date": "2026-03-20"})

        resp = await client.get("/api/todos", params={"date": "2026-03-20"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 2


@pytest.mark.anyio
async def test_update_todo():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/api/todos", json={"title": "업데이트", "due_date": "2026-03-21"})
        todo_id = create_resp.json()["id"]

        resp = await client.patch(f"/api/todos/{todo_id}", json={"is_completed": True})
        assert resp.status_code == 200
        assert resp.json()["is_completed"] == 1


@pytest.mark.anyio
async def test_delete_todo():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/api/todos", json={"title": "삭제", "due_date": "2026-03-22"})
        todo_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/todos/{todo_id}")
        assert resp.status_code == 204


@pytest.mark.anyio
async def test_delete_nonexistent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/api/todos/99999")
        assert resp.status_code == 404
