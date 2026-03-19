import re
from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
from typing import Optional

import dateparser


@dataclass
class ParsedTodo:
    title: str
    due_date: date
    due_time: Optional[time] = None


# 한국어 상대 날짜 패턴
RELATIVE_DATE_PATTERNS = {
    "오늘": 0,
    "내일": 1,
    "모레": 2,
    "글피": 3,
}

# 요일 매핑
DAY_NAMES = {
    "월요일": 0, "화요일": 1, "수요일": 2, "목요일": 3,
    "금요일": 4, "토요일": 5, "일요일": 6,
}

# 시간대 매핑
TIME_WORDS = {
    "아침": time(8, 0),
    "오전": None,  # 수식어로만 사용
    "점심": time(12, 0),
    "오후": None,  # 수식어로만 사용
    "저녁": time(18, 0),
    "밤": time(21, 0),
}


def _extract_korean_date(text: str, now: datetime):
    """한국어 텍스트에서 날짜를 추출하고 나머지 텍스트를 반환"""
    remaining = text

    # 상대 날짜 (오늘, 내일, 모레)
    for keyword, delta in RELATIVE_DATE_PATTERNS.items():
        if keyword in remaining:
            remaining = remaining.replace(keyword, "", 1)
            return now.date() + timedelta(days=delta), remaining

    # 요일 (금요일, 월요일 등)
    for day_name, day_num in DAY_NAMES.items():
        if day_name in remaining:
            remaining = remaining.replace(day_name, "", 1)
            remaining = remaining.replace("까지", "", 1)
            remaining = remaining.replace("이번주", "", 1)
            remaining = remaining.replace("다음주", "", 1)
            days_ahead = day_num - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return now.date() + timedelta(days=days_ahead), remaining

    # N월 N일 패턴
    date_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', remaining)
    if date_match:
        month = int(date_match.group(1))
        day = int(date_match.group(2))
        remaining = remaining[:date_match.start()] + remaining[date_match.end():]
        year = now.year
        target = date(year, month, day)
        if target < now.date():
            target = date(year + 1, month, day)
        return target, remaining

    return None, remaining


def _extract_time(text: str):
    """텍스트에서 시간을 추출하고 나머지 텍스트를 반환"""
    remaining = text

    # "오전/오후 N시" 패턴
    am_pm_match = re.search(r'(오전|오후)\s*(\d{1,2})시', remaining)
    if am_pm_match:
        period = am_pm_match.group(1)
        hour = int(am_pm_match.group(2))
        if period == "오후" and hour < 12:
            hour += 12
        remaining = remaining[:am_pm_match.start()] + remaining[am_pm_match.end():]
        return time(hour, 0), remaining

    # "N시" 패턴 (단독)
    time_match = re.search(r'(\d{1,2})시(?:\s*(\d{1,2})분)?', remaining)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        # 1~6시는 오후로 간주
        if 1 <= hour <= 6:
            hour += 12
        remaining = remaining[:time_match.start()] + remaining[time_match.end():]
        return time(hour, minute), remaining

    # 시간대 단어 (아침, 점심, 저녁, 밤) — 독립된 단어일 때만
    for word, t in TIME_WORDS.items():
        if t is None:
            continue
        match = re.search(rf'(?<!\S){re.escape(word)}(?!\S)', remaining)
        if match:
            remaining = remaining[:match.start()] + remaining[match.end():]
            return t, remaining

    # "오전", "오후"만 있는 경우 제거
    for word in ["오전", "오후"]:
        if word in remaining:
            remaining = remaining.replace(word, "", 1)

    return None, remaining


def parse_todo(text: str, now: Optional[datetime] = None) -> ParsedTodo:
    if now is None:
        now = datetime.now()

    # 1. 날짜 추출
    due_date, remaining = _extract_korean_date(text, now)

    # 2. 시간 추출
    due_time, remaining = _extract_time(remaining)

    # 3. 남은 텍스트가 제목
    title = remaining.strip()
    # 불필요한 조사/접속사 정리
    title = re.sub(r'^[에서의을를이가은는]\s*', '', title)
    title = title.strip()

    # 날짜를 못 찾으면 오늘
    if due_date is None:
        due_date = now.date()

    # 제목이 비어있으면 원본 사용
    if not title:
        title = text.strip()

    return ParsedTodo(title=title, due_date=due_date, due_time=due_time)
