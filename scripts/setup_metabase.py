#!/usr/bin/env python3
"""
Автоматическая настройка Metabase:
  - первичный setup (admin)
  - подключение PostgreSQL
  - 5 SQL-вопросов
  - дашборд с фильтрами

Использование:
  python3 scripts/setup_metabase.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:3000"
ADMIN_EMAIL = "admin@it-resume.local"
ADMIN_PASSWORD = "Analytics2025!"
ADMIN_NAME = "Analytics"
ADMIN_LAST_NAME = "Admin"
SITE_NAME = "IT Resume Analytics"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_DIR = PROJECT_ROOT / "sql" / "metrics"

QUESTIONS = [
    {
        "file": "01_daily_activity.sql",
        "name": "Ежедневная активность студентов",
        "description": "Уникальные студенты с ≥1 попыткой за день",
        "display": "line",
        "dimensions": ["activity_date"],
        "metrics": ["active_students"],
    },
    {
        "file": "02_course_funnel.sql",
        "name": "Конверсия по этапам курса",
        "description": "Воронка от регистрации до завершения курса",
        "display": "funnel",
        "dimensions": ["stage"],
        "metrics": ["students"],
    },
    {
        "file": "03_task_difficulty.sql",
        "name": "Сложность задач: время и попытки",
        "description": "Среднее время, попытки и % успеха по задачам",
        "display": "bar",
        "dimensions": ["task_name"],
        "metrics": ["avg_attempts"],
    },
    {
        "file": "04_student_progress.sql",
        "name": "Индивидуальный прогресс студентов",
        "description": "Таблица прогресса с цветовым статусом",
        "display": "table",
        "dimensions": [],
        "metrics": [],
    },
    {
        "file": "05_client_benchmark.sql",
        "name": "Позиция клиента относительно других",
        "description": "Completion rate по всем корпоративным клиентам",
        "display": "bar",
        "dimensions": ["client_name"],
        "metrics": ["completion_rate_pct"],
    },
]

DASHBOARD_NAME = "Корпоративный клиент IT Resume"
DASHBOARD_DESCRIPTION = (
    "Дашборд для мониторинга обучения сотрудников корпоративного заказчика. "
    "Фильтры: клиент, период."
)


class MetabaseClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_id: str | None = None

    def _request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        *,
        auth: bool = True,
    ) -> dict | list:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        if auth and self.session_id:
            headers["X-Metabase-Session"] = self.session_id

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path} → HTTP {exc.code}: {body}") from exc

    def wait_until_ready(self, timeout_sec: int = 300) -> None:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                url = f"{self.base_url}/api/health"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=10) as resp:
                    health = json.loads(resp.read().decode("utf-8"))
                    if health.get("status") == "ok":
                        return
            except urllib.error.HTTPError as exc:
                if exc.code == 503:
                    time.sleep(5)
                    continue
            except Exception:
                pass
            time.sleep(5)
        raise TimeoutError("Metabase не ответил за отведённое время")

    def is_setup_complete(self) -> bool:
        props = self._request("GET", "/api/session/properties", auth=False)
        return props.get("has-user-setup-token") is False or props.get("setup-token") is None

    def setup_admin(self) -> None:
        props = self._request("GET", "/api/session/properties", auth=False)
        token = props.get("setup-token")
        if not token:
            print("  Setup уже выполнен, пропускаем")
            return

        payload = {
            "token": token,
            "user": {
                "first_name": ADMIN_NAME,
                "last_name": ADMIN_LAST_NAME,
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "site_name": SITE_NAME,
            },
            "prefs": {
                "site_name": SITE_NAME,
                "site_locale": "ru",
                "allow_tracking": False,
            },
        }
        self._request("POST", "/api/setup", payload, auth=False)
        print(f"  Admin создан: {ADMIN_EMAIL}")

    def login(self) -> None:
        resp = self._request(
            "POST",
            "/api/session",
            {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            auth=False,
        )
        self.session_id = resp["id"]
        print("  Авторизация успешна")

    def get_or_create_database(self) -> int:
        dbs = self._request("GET", "/api/database")
        for db in dbs.get("data", dbs if isinstance(dbs, list) else []):
            if db.get("name") == "IT Resume Analytics":
                print(f"  База уже подключена (id={db['id']})")
                return db["id"]

        payload = {
            "engine": "postgres",
            "name": "IT Resume Analytics",
            "details": {
                "host": "postgres",
                "port": 5432,
                "dbname": "it_resume_analytics",
                "user": "analytics",
                "password": "analytics",
                "ssl": False,
            },
            "auto_run_queries": True,
            "is_full_sync": True,
            "schedules": {},
        }
        db = self._request("POST", "/api/database", payload)
        db_id = db["id"]
        print(f"  База подключена (id={db_id}), синхронизация...")
        self._wait_for_sync(db_id)
        return db_id

    def _wait_for_sync(self, db_id: int) -> None:
        for _ in range(30):
            db = self._request("GET", f"/api/database/{db_id}")
            if db.get("initial_sync_status") == "complete":
                return
            time.sleep(2)

    def load_sql(self, filename: str) -> str:
        text = (METRICS_DIR / filename).read_text(encoding="utf-8")
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("--")]
        return "\n".join(lines).strip()

    def create_question(self, db_id: int, spec: dict) -> int:
        existing = self._find_card_by_name(spec["name"])
        if existing:
            print(f"  Вопрос «{spec['name']}» уже есть (id={existing})")
            return existing

        template_tags = {}
        sql = self.load_sql(spec["file"])

        for var_name, var_type, default in [
            ("client_id", "number", "1"),
            ("date_from", "date", "2025-10-01"),
            ("date_to", "date", "2026-05-01"),
        ]:
            if f"{{{{{var_name}}}}}" in sql:
                template_tags[var_name] = {
                    "id": var_name,
                    "name": var_name,
                    "display-name": var_name.replace("_", " ").title(),
                    "type": var_type,
                    "required": True,
                    "default": default,
                }

        viz = {
            "display": spec["display"],
            "dataset_query": {
                "type": "native",
                "database": db_id,
                "native": {
                    "query": sql,
                    "template-tags": template_tags,
                },
            },
            "visualization_settings": build_viz_settings(spec),
            "name": spec["name"],
            "description": spec["description"],
        }

        card = self._request("POST", "/api/card", viz)
        print(f"  Создан вопрос «{spec['name']}» (id={card['id']})")
        return card["id"]

    def _find_card_by_name(self, name: str) -> int | None:
        cards = self._request("GET", "/api/card")
        for card in cards:
            if card.get("name") == name:
                return card["id"]
        return None

    def create_dashboard(self, card_ids: list[int]) -> int:
        existing = self._find_dashboard_by_name(DASHBOARD_NAME)
        if existing:
            print(f"  Дашборд уже существует (id={existing})")
            return existing

        dash = self._request(
            "POST",
            "/api/dashboard",
            {
                "name": DASHBOARD_NAME,
                "description": DASHBOARD_DESCRIPTION,
            },
        )
        dash_id = dash["id"]

        cards_layout = [
            (card_ids[0], 0, 0, 18, 6),   # line — full width top
            (card_ids[1], 0, 6, 9, 6),    # funnel
            (card_ids[2], 9, 6, 9, 6),    # bar difficulty
            (card_ids[4], 0, 12, 18, 5),  # benchmark
            (card_ids[3], 0, 17, 18, 8),  # table progress
        ]

        dashcards = []
        for idx, (card_id, col, row, size_x, size_y) in enumerate(cards_layout):
            dashcards.append(
                {
                    "id": -(idx + 1),
                    "card_id": card_id,
                    "row": row,
                    "col": col,
                    "size_x": size_x,
                    "size_y": size_y,
                    "parameter_mappings": build_parameter_mappings(card_id, idx),
                }
            )

        self._request(
            "PUT",
            f"/api/dashboard/{dash_id}",
            {
                "name": DASHBOARD_NAME,
                "description": DASHBOARD_DESCRIPTION,
                "parameters": [
                    {
                        "id": "client_id",
                        "name": "Клиент (ID)",
                        "slug": "client_id",
                        "type": "number/=",
                        "default": 1,
                    },
                    {
                        "id": "date_from",
                        "name": "Дата с",
                        "slug": "date_from",
                        "type": "date/single",
                        "default": "2025-10-01",
                    },
                    {
                        "id": "date_to",
                        "name": "Дата по",
                        "slug": "date_to",
                        "type": "date/single",
                        "default": "2026-05-01",
                    },
                ],
                "dashcards": dashcards,
            },
        )

        print(f"  Дашборд создан (id={dash_id})")
        return dash_id

    def _find_dashboard_by_name(self, name: str) -> int | None:
        dashboards = self._request("GET", "/api/dashboard")
        for dash in dashboards:
            if dash.get("name") == name:
                return dash["id"]
        return None


def build_viz_settings(spec: dict) -> dict:
    display = spec["display"]
    if display == "line":
        return {
            "graph.dimensions": ["activity_date"],
            "graph.metrics": ["active_students"],
            "graph.x_axis.title_text": "Дата",
            "graph.y_axis.title_text": "Студентов",
        }
    if display == "funnel":
        return {
            "funnel.dimension": "stage",
            "funnel.metric": "students",
        }
    if display == "bar":
        if "бенчмарк" in spec["name"].lower() or "позиция" in spec["name"].lower():
            return {
                "graph.dimensions": ["client_name"],
                "graph.metrics": ["completion_rate_pct"],
                "graph.x_axis.title_text": "Клиент",
                "graph.y_axis.title_text": "% завершивших курс",
            }
        return {
            "graph.dimensions": ["task_name"],
            "graph.metrics": ["avg_attempts"],
            "graph.x_axis.title_text": "Задача",
            "graph.y_axis.title_text": "Среднее число попыток",
        }
    return {}


def build_parameter_mappings(card_id: int, layout_idx: int) -> list[dict]:
    """Привязка фильтров дашборда к template-tags вопросов."""
    mappings = [
        {
            "parameter_id": "client_id",
            "card_id": card_id,
            "target": ["variable", ["template-tag", "client_id"]],
        },
    ]
    if layout_idx in (0, 2):  # daily activity, task difficulty
        mappings.extend([
            {
                "parameter_id": "date_from",
                "card_id": card_id,
                "target": ["variable", ["template-tag", "date_from"]],
            },
            {
                "parameter_id": "date_to",
                "card_id": card_id,
                "target": ["variable", ["template-tag", "date_to"]],
            },
        ])
    return mappings


def main() -> int:
    print("=== Настройка Metabase ===\n")
    client = MetabaseClient(BASE_URL)

    print("[1/5] Ожидание запуска Metabase...")
    client.wait_until_ready()

    print("[2/5] Первичный setup...")
    client.setup_admin()

    print("[3/5] Авторизация...")
    client.login()

    print("[4/5] Подключение базы и создание вопросов...")
    db_id = client.get_or_create_database()
    card_ids = [client.create_question(db_id, spec) for spec in QUESTIONS]

    print("[5/5] Сборка дашборда...")
    dash_id = client.create_dashboard(card_ids)

    print("[6/6] Добавление выводов → рекомендаций...")
    import subprocess
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "update_dashboard_insights.py")],
        check=True,
    )

    print("\n=== Готово ===")
    print(f"URL:      {BASE_URL}/dashboard/{dash_id}")
    print(f"Login:    {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")
    print("\nФильтры на дашборде: Клиент (ID), Дата с, Дата по")
    print("Auto-refresh: Dashboard → ⋮ → Edit → включите обновление (1 час)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nОшибка: {exc}", file=sys.stderr)
        raise SystemExit(1)
