import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers.todos import router as todos_router
from app.routers.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Telegram bot setup (skip if no token)
    if settings.telegram_bot_token:
        from app.bot import create_bot_app
        import app.routers.webhook as wh

        bot_app = create_bot_app()
        await bot_app.initialize()
        wh.bot_app = bot_app

        if settings.webhook_url:
            await bot_app.bot.set_webhook(f"{settings.webhook_url}/webhook/telegram")

    # Scheduler setup (skip if no token)
    scheduler = None
    if settings.telegram_bot_token:
        from app.scheduler import create_scheduler
        scheduler = create_scheduler()
        scheduler.start()

    yield

    if scheduler:
        scheduler.shutdown()

    if settings.telegram_bot_token:
        if settings.webhook_url:
            await bot_app.bot.delete_webhook()
        await bot_app.shutdown()


app = FastAPI(title="투두메이트", lifespan=lifespan)
app.include_router(todos_router)
app.include_router(webhook_router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
