from datetime import date, time, datetime
from typing import Optional

from pydantic import BaseModel


class TodoCreate(BaseModel):
    title: str
    due_date: date
    due_time: Optional[time] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    is_completed: Optional[bool] = None


class TodoResponse(BaseModel):
    id: int
    title: str
    due_date: date
    due_time: Optional[time] = None
    is_completed: bool = False
    created_at: datetime
