from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import httpx

from app.config import settings

SYSTEM_PROMPT = """너는 투두(할일) 관리 봇의 의도 분석기야.
사용자 메시지를 분석해서 JSON으로 응답해.

오늘 날짜: {today}

## 응답 형식

반드시 아래 JSON 형식으로만 응답해. 설명 없이 JSON만.

### 할일 추가 (한 개 또는 여러 개)
{{"intent": "add", "todos": [{{"title": "할일 제목", "due_date": "YYYY-MM-DD", "due_time": "HH:MM" 또는 null}}]}}

### 완료 처리
{{"intent": "done", "todo_id": 번호}}

### 삭제
{{"intent": "delete", "todo_id": 번호}}

### 오늘 할일 조회
{{"intent": "list_today"}}

### 내일 할일 조회
{{"intent": "list_tomorrow"}}

### 이해 불가
{{"intent": "unknown", "message": "이해하지 못한 이유"}}

## 규칙
- "내일"은 오늘 +1일로 계산
- "모레"는 오늘 +2일
- 날짜 언급 없으면 오늘 날짜 사용
- 시간 언급 없으면 due_time은 null
- "3시"처럼 애매하면 문맥상 오후(15:00)로 해석
- 여러 할일이 한 메시지에 있으면 todos 배열에 모두 넣어
- "N번 지워", "N번 삭제" → delete
- "N번 완료", "N번 했어", "N번 끝" → done
- "오늘 뭐해", "할일 보여줘" → list_today
- "내일 뭐해" → list_tomorrow
"""


async def parse_intent(text: str) -> dict:
    """Claude API로 사용자 메시지의 의도를 파악한다."""
    today = datetime.now().strftime("%Y-%m-%d (%A)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1024,
                "system": SYSTEM_PROMPT.format(today=today),
                "messages": [{"role": "user", "content": text}],
            },
        )
        response.raise_for_status()
        data = response.json()

    content = data["content"][0]["text"]

    # JSON 파싱 (코드블록 감싸기 대응)
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    return json.loads(content)
