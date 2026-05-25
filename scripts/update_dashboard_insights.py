#!/usr/bin/env python3
"""Добавляет на дашборд Metabase текстовые блоки «Выводы → Рекомендации»."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE_URL = "http://localhost:3000"
ADMIN_EMAIL = "admin@it-resume.local"
ADMIN_PASSWORD = "Analytics2025!"
DASHBOARD_ID = 1

HEADER_TEXT = """### Корпоративный клиент IT Resume
**Клиент:** ООО ТехноСофт · **Студентов:** 15 · **Период:** окт 2025 — май 2026

Дашборд для мониторинга прогресса корпоративного обучения. Используйте фильтры выше."""

FOOTER_TEXT = """### Итог для руководства
Все 15 сотрудников начали обучение и прошли Python, но до SQL дошли только **7 из 15**, а курс целиком — **никто**.

**Приоритетные действия:** re-engagement кампания · доработка модуля SQL · 1:1-работа куратора с отстающими."""

INSIGHTS = {
    1: """### Выводы → Рекомендации · Активность

**Выводы**
- Средняя активность — **2,8 студента/день** из 15 (~19%)
- Пик — **ноябрь 2025**, далее вовлечённость падает
- Обучение не встроено в рабочий ритм

**Рекомендации**
- Слоты обучения **1–2 ч/нед** в рабочее время
- Напоминания куратору о неактивных **>7 дней**
- KPI: **DAU/WAU ≥ 40%**""",

    2: """### Выводы → Рекомендации · Воронка

**Выводы**
- **100%** прошли Python, **47%** — SQL, **0%** — курс
- Главное «узкое горло» — **модуль 2 (SQL)**
- Отвал на переходе Python → SQL

**Рекомендации**
- Блок «SQL для Python-разработчиков»
- **Office hours** 2 недели после старта SQL
- KPI: **≥70%** прохождения модуля 2 за 30 дней""",

    3: """### Выводы → Рекомендации · Сложность задач

**Выводы**
- **JOIN** — 2,4 попытки, 22% успеха
- **GROUP BY** — 2,4 попытки, 19% успеха
- **Ошибки API** — 2,6 попытки, 0% успеха

**Рекомендации**
- Разбить JOIN/GROUP BY на 2 уровня
- Подсказки и примеры перед практикой
- Перенести API-задачи после REST-блока""",

    5: """### Выводы → Рекомендации · Бенчмарк

**Выводы**
- **0% completion** у всех клиентов — системная проблема
- Модуль 1 проходят все — барьер в **середине курса**
- ТехноСофт не отстаёт от рынка по финальному KPI

**Рекомендации**
- Промежуточная **сертификация** после модуля 3
- **Custdev** с 3 корпоративными клиентами
- Бенчмарк «завершили модуль N» вместо только финала""",

    4: """### Выводы → Рекомендации · Прогресс студентов

**Выводы**
- Средний прогресс — **43%** (диапазон 27–60%)
- Лидеры — **60%**, порог «Готов» (80%) — **0 человек**
- Все 15 студентов — статус **«Отстаёт»** (>14 дней)

**Рекомендации**
- Индив. планы для **5 студентов** с progress <40%
- **1:1-созвоны** куратора в течение 2 недель
- KPI: **≥50%** сотрудников с progress >50%""",
}


def api(
    method: str,
    path: str,
    session_id: str = "",
    payload: dict | None = None,
    *,
    auth: bool = True,
) -> dict:
    headers = {"Content-Type": "application/json"}
    if auth and session_id:
        headers["X-Metabase-Session"] = session_id
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} → {exc.code}: {exc.read().decode()}") from exc


def login() -> str:
    resp = api(
        "POST",
        "/api/session",
        payload={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        auth=False,
    )
    return resp["id"]


def text_card(card_id: int, row: int, col: int, size_x: int, size_y: int, text: str) -> dict:
    return {
        "id": card_id,
        "card_id": None,
        "row": row,
        "col": col,
        "size_x": size_x,
        "size_y": size_y,
        "parameter_mappings": [],
        "visualization_settings": {
            "text": text,
            "virtual_card": {
                "display": "text",
                "dataset_query": {},
                "visualization_settings": {},
            },
        },
    }


def chart_card(
    dashcard_id: int,
    card_id: int,
    row: int,
    col: int,
    size_x: int,
    size_y: int,
    parameter_mappings: list,
) -> dict:
    return {
        "id": dashcard_id,
        "card_id": card_id,
        "row": row,
        "col": col,
        "size_x": size_x,
        "size_y": size_y,
        "parameter_mappings": parameter_mappings,
    }


def rebuild_dashboard(session_id: str) -> None:
    dash = api("GET", f"/api/dashboard/{DASHBOARD_ID}", session_id)
    charts = {dc["card_id"]: dc for dc in dash["dashcards"] if dc.get("card_id")}

    layout = [
        text_card(-1, 0, 0, 18, 2, HEADER_TEXT),
        chart_card(-2, 1, 2, 0, 18, 6, charts[1]["parameter_mappings"]),
        text_card(-3, 8, 0, 18, 4, INSIGHTS[1]),
        chart_card(-4, 2, 12, 0, 9, 6, charts[2]["parameter_mappings"]),
        text_card(-5, 18, 0, 9, 4, INSIGHTS[2]),
        chart_card(-6, 3, 12, 9, 9, 6, charts[3]["parameter_mappings"]),
        text_card(-7, 18, 9, 9, 4, INSIGHTS[3]),
        chart_card(-8, 5, 22, 0, 18, 5, charts[5]["parameter_mappings"]),
        text_card(-9, 27, 0, 18, 4, INSIGHTS[5]),
        chart_card(-10, 4, 31, 0, 18, 8, charts[4]["parameter_mappings"]),
        text_card(-11, 39, 0, 18, 4, INSIGHTS[4]),
        text_card(-12, 43, 0, 18, 3, FOOTER_TEXT),
    ]

    payload = {
        "name": dash["name"],
        "description": dash.get("description"),
        "parameters": dash.get("parameters", []),
        "dashcards": layout,
    }
    api("PUT", f"/api/dashboard/{DASHBOARD_ID}", session_id, payload)


def main() -> int:
    print("Обновление дашборда: выводы → рекомендации...")
    session_id = login()
    rebuild_dashboard(session_id)
    print(f"Готово: {BASE_URL}/dashboard/{DASHBOARD_ID}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        raise SystemExit(1)
