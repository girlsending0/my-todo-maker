from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from app.config import settings
from app.database import get_db
from app.crud import get_todos_by_date, get_incomplete_todos_for_date


async def _send_telegram(text: str):
    """Send a message via Telegram Bot API."""
    import httpx
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": settings.telegram_chat_id,
            "text": text,
        })


async def morning_summary():
    """아침 07:00 — 오늘 할 일 요약"""
    today = datetime.now(pytz.timezone(settings.timezone)).date()
    db = await get_db()
    try:
        todos = await get_todos_by_date(db, today)
    finally:
        await db.close()

    if not todos:
        text = f"☀️ 좋은 아침! ({today.strftime('%m/%d')})\n오늘 등록된 할 일이 없습니다."
    else:
        lines = [f"☀️ 좋은 아침! 오늘 ({today.strftime('%m/%d')}) 할 일 {len(todos)}개:"]
        for t in todos:
            time_str = f" {t['due_time'][:5]}" if t.get("due_time") else ""
            lines.append(f"  ⬜ {t['title']}{time_str}")
        text = "\n".join(lines)

    await _send_telegram(text)


async def evening_reminder():
    """저녁 21:00 — 미완료 리마인더"""
    today = datetime.now(pytz.timezone(settings.timezone)).date()
    db = await get_db()
    try:
        incomplete = await get_incomplete_todos_for_date(db, today)
    finally:
        await db.close()

    if not incomplete:
        text = "🎉 오늘 할 일을 모두 완료했습니다! 수고했어요."
    else:
        lines = [f"🔔 아직 안 한 일이 {len(incomplete)}개 있어요:"]
        for t in incomplete:
            lines.append(f"  ⬜ {t['title']}")
        text = "\n".join(lines)

    await _send_telegram(text)


def create_scheduler() -> AsyncIOScheduler:
    tz = pytz.timezone(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        morning_summary,
        CronTrigger(hour=7, minute=0, timezone=tz),
        id="morning_summary",
    )
    scheduler.add_job(
        evening_reminder,
        CronTrigger(hour=21, minute=0, timezone=tz),
        id="evening_reminder",
    )

    return scheduler
