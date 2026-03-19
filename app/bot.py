from __future__ import annotations

from datetime import datetime, time

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from app.config import settings
from app.database import get_db
from app.models import TodoCreate, TodoUpdate
from app.crud import create_todo, get_todos_by_date, update_todo, delete_todo, get_incomplete_todos_for_date
from app.intent import parse_intent


def _is_authorized(update: Update) -> bool:
    return update.effective_chat.id == settings.telegram_chat_id


def _format_todo_list(todos: list[dict], title: str) -> str:
    if not todos:
        return f"{title}\n등록된 할 일이 없습니다."

    lines = [title]
    for t in todos:
        status = "✅" if t["is_completed"] else "⬜"
        time_str = f" {t['due_time'][:5]}" if t.get("due_time") else ""
        lines.append(f"{status} [{t['id']}] {t['title']}{time_str}")
    return "\n".join(lines)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        "투두메이트에 오신 것을 환영합니다!\n\n"
        "사용법:\n"
        "- 자연어로 할 일 입력: '내일 3시 병원'\n"
        "- /today - 오늘 할 일\n"
        "- /tomorrow - 내일 할 일\n"
        "- /done 번호 - 완료 처리\n"
        "- /delete 번호 - 삭제"
    )


async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    db = await get_db()
    try:
        todos = await get_todos_by_date(db, datetime.now().date())
        text = _format_todo_list(todos, f"📋 오늘 ({datetime.now().strftime('%m/%d')}) 할 일:")
        await update.message.reply_text(text)
    finally:
        await db.close()


async def tomorrow_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    from datetime import timedelta
    tomorrow = datetime.now().date() + timedelta(days=1)
    db = await get_db()
    try:
        todos = await get_todos_by_date(db, tomorrow)
        text = _format_todo_list(todos, f"📋 내일 ({tomorrow.strftime('%m/%d')}) 할 일:")
        await update.message.reply_text(text)
    finally:
        await db.close()


async def done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    if not context.args:
        await update.message.reply_text("사용법: /done 번호")
        return
    try:
        todo_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("올바른 번호를 입력해주세요.")
        return

    db = await get_db()
    try:
        result = await update_todo(db, todo_id, TodoUpdate(is_completed=True))
        if result:
            await update.message.reply_text(f"✅ 완료: {result['title']}")
        else:
            await update.message.reply_text("해당 할 일을 찾을 수 없습니다.")
    finally:
        await db.close()


async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    if not context.args:
        await update.message.reply_text("사용법: /delete 번호")
        return
    try:
        todo_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("올바른 번호를 입력해주세요.")
        return

    db = await get_db()
    try:
        success = await delete_todo(db, todo_id)
        if success:
            await update.message.reply_text("🗑 삭제했습니다.")
        else:
            await update.message.reply_text("해당 할 일을 찾을 수 없습니다.")
    finally:
        await db.close()


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return

    try:
        result = await parse_intent(update.message.text)
    except Exception:
        await update.message.reply_text("메시지를 이해하지 못했어요. 다시 시도해주세요.")
        return

    intent = result.get("intent")

    if intent == "add":
        db = await get_db()
        try:
            lines = []
            for item in result.get("todos", []):
                due_time = None
                if item.get("due_time"):
                    h, m = item["due_time"].split(":")
                    due_time = time(int(h), int(m))
                todo = TodoCreate(
                    title=item["title"],
                    due_date=datetime.strptime(item["due_date"], "%Y-%m-%d").date(),
                    due_time=due_time,
                )
                created = await create_todo(db, todo)
                time_str = f" {item['due_time']}" if item.get("due_time") else ""
                lines.append(f"📝 {created['title']} ({item['due_date'][5:]}{time_str})")
            await update.message.reply_text("추가했어요!\n" + "\n".join(lines))
        finally:
            await db.close()

    elif intent == "done":
        todo_id = result.get("todo_id")
        db = await get_db()
        try:
            updated = await update_todo(db, todo_id, TodoUpdate(is_completed=True))
            if updated:
                await update.message.reply_text(f"✅ 완료: {updated['title']}")
            else:
                await update.message.reply_text("해당 할 일을 찾을 수 없습니다.")
        finally:
            await db.close()

    elif intent == "delete":
        todo_id = result.get("todo_id")
        db = await get_db()
        try:
            success = await delete_todo(db, todo_id)
            if success:
                await update.message.reply_text("🗑 삭제했습니다.")
            else:
                await update.message.reply_text("해당 할 일을 찾을 수 없습니다.")
        finally:
            await db.close()

    elif intent == "list_today":
        db = await get_db()
        try:
            todos = await get_todos_by_date(db, datetime.now().date())
            text = _format_todo_list(todos, f"📋 오늘 ({datetime.now().strftime('%m/%d')}) 할 일:")
            await update.message.reply_text(text)
        finally:
            await db.close()

    elif intent == "list_tomorrow":
        from datetime import timedelta
        tomorrow = datetime.now().date() + timedelta(days=1)
        db = await get_db()
        try:
            todos = await get_todos_by_date(db, tomorrow)
            text = _format_todo_list(todos, f"📋 내일 ({tomorrow.strftime('%m/%d')}) 할 일:")
            await update.message.reply_text(text)
        finally:
            await db.close()

    else:
        await update.message.reply_text("이해하지 못했어요. 할 일을 추가하거나 /today, /done 등을 사용해주세요.")


def create_bot_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("today", today_handler))
    app.add_handler(CommandHandler("tomorrow", tomorrow_handler))
    app.add_handler(CommandHandler("done", done_handler))
    app.add_handler(CommandHandler("delete", delete_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    return app
