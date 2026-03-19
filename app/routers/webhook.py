from fastapi import APIRouter, Request
from telegram import Update

router = APIRouter()

# bot_app is set by main.py during startup
bot_app = None


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    if bot_app is None:
        return {"error": "Bot not initialized"}

    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}
