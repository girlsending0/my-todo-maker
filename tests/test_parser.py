import pytest
from datetime import date, time, datetime

from app.parser import parse_todo


# 고정된 "지금" 시간으로 테스트
NOW = datetime(2026, 3, 18, 20, 0)  # 2026-03-18 20:00 (수요일)


def test_tomorrow_with_time():
    result = parse_todo("내일 3시 병원", now=NOW)
    assert result.title == "병원"
    assert result.due_date == date(2026, 3, 19)
    assert result.due_time == time(15, 0)


def test_deadline_with_day():
    result = parse_todo("금요일까지 보고서 제출", now=NOW)
    assert result.title == "보고서 제출"
    assert result.due_date == date(2026, 3, 20)  # 이번주 금요일


def test_today_evening():
    result = parse_todo("오늘 저녁 장보기", now=NOW)
    assert result.title == "장보기"
    assert result.due_date == date(2026, 3, 18)


def test_specific_date():
    result = parse_todo("12월 25일 크리스마스 파티", now=NOW)
    assert result.title == "크리스마스 파티"
    assert result.due_date == date(2026, 12, 25)


def test_no_date_defaults_to_today():
    result = parse_todo("빨래하기", now=NOW)
    assert result.title == "빨래하기"
    assert result.due_date == date(2026, 3, 18)
    assert result.due_time is None


def test_day_after_tomorrow():
    result = parse_todo("모레 점심약속", now=NOW)
    assert result.title == "점심약속"
    assert result.due_date == date(2026, 3, 20)


def test_tomorrow_morning():
    result = parse_todo("내일 오전 10시 회의", now=NOW)
    assert result.title == "회의"
    assert result.due_date == date(2026, 3, 19)
    assert result.due_time == time(10, 0)
