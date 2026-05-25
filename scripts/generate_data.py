#!/usr/bin/env python3
"""Generate synthetic CSV datasets for IT Resume corporate analytics demo."""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_DATE = datetime(2025, 10, 1)

CLIENTS = [
    (1, "ООО ТехноСофт", "Enterprise", "2025-01-01", "2026-12-31"),
    (2, "АО ФинГруп", "Business", "2025-03-01", "2026-03-01"),
    (3, "ИП Рогов", "Starter", "2025-06-01", "2026-06-01"),
    (4, "ООО МедТech", "Enterprise", "2024-09-01", "2025-09-01"),
    (5, "ЗАО Логистика+", "Business", "2025-02-01", "2026-02-01"),
]

MODULES = [
    (1, 1, "Python: основы", 1),
    (2, 1, "SQL и базы данных", 2),
    (3, 1, "API и интеграции", 3),
    (4, 1, "DevOps: основы", 4),
]

TASKS = [
    (1, 1, "Переменные и типы данных", 1),
    (2, 1, "Условия и циклы", 2),
    (3, 1, "Функции", 3),
    (4, 2, "SELECT и фильтрация", 1),
    (5, 2, "JOIN-запросы", 2),
    (6, 2, "Агрегации и GROUP BY", 3),
    (7, 2, "Подзапросы", 4),
    (8, 3, "REST API: GET/POST", 1),
    (9, 3, "Аутентификация", 2),
    (10, 3, "Обработка ошибок API", 3),
    (11, 3, "Интеграционный проект", 4),
    (12, 4, "Docker: контейнеры", 1),
    (13, 4, "CI/CD pipeline", 2),
    (14, 4, "Мониторинг", 3),
    (15, 4, "Финальный проект", 4),
]

# Hard tasks (module 2 JOIN, module 3 auth) get more attempts
HARD_TASKS = {5, 6, 9, 10}

NAMES = [
    "Иванов Алексей", "Петрова Мария", "Сидоров Дмитрий", "Козлова Анна",
    "Новиков Сергей", "Морозова Елена", "Волков Андрей", "Соколова Ольга",
    "Лебедев Никита", "Кузнецова Татьяна", "Попов Максим", "Смирнова Юлия",
    "Федоров Артём", "Васильева Ксения", "Михайлов Павел", "Николаев Роман",
    "Орлова Виктория", "Андреев Игорь", "Захарова Алина", "Егоров Константин",
    "Романова Дарья", "Григорьев Владислав", "Белова Светлана", "Комаров Олег",
    "Тихонова Надежда", "Баранов Евгений", "Фомина Полина", "Данилов Глеб",
    "Жукова Вероника", "Семёнов Тимур", "Макарова Людмила", "Киселёв Арсений",
    "Абрамова Екатерина", "Медведев Стас", "Калинина Ульяна", "Тарасов Денис",
    "Борисова Карина", "Антонов Матвей", "Гусев Ярослав", "Степанова Алёна",
    "Крылов Руслан", "Виноградова Марина", "Лазарев Илья", "Павлова Софья",
    "Сорокин Георгий", "Трофимова Валерия", "Климов Артур", "Рыбакова Жанна",
    "Голубев Степан", "Мельникова Инна", "Богданов Филипп", "Ковалева Агата",
    "Зайцев Лев", "Савина Милана", "Марков Эдуард", "Назарова Регина",
    "Осипов Тихон", "Чернова Лариса", "Суханов Марк", "Яковлева Алиса",
]

CLIENT_PROFILES = {
    1: {"size": 15, "completion_bias": 0.55, "activity": 0.85},
    2: {"size": 12, "completion_bias": 0.72, "activity": 0.90},
    3: {"size": 8, "completion_bias": 0.30, "activity": 0.50},
    4: {"size": 16, "completion_bias": 0.65, "activity": 0.80},
    5: {"size": 10, "completion_bias": 0.48, "activity": 0.70},
}


def write_csv(filename, headers, rows):
    path = DATA_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")


def generate_users():
    rows = []
    user_id = 1
    name_idx = 0
    for client_id, profile in CLIENT_PROFILES.items():
        for i in range(profile["size"]):
            created = BASE_DATE - timedelta(days=random.randint(5, 60))
            rows.append((
                user_id,
                client_id,
                NAMES[name_idx % len(NAMES)],
                f"user{user_id}@client{client_id}.example.com",
                "student",
                created.strftime("%Y-%m-%d %H:%M:%S"),
            ))
            user_id += 1
            name_idx += 1
        rows.append((
            user_id,
            client_id,
            f"Куратор клиента {client_id}",
            f"curator{client_id}@example.com",
            "curator",
            (BASE_DATE - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S"),
        ))
        user_id += 1
    return rows


def task_list_for_progress(completed_count):
    ordered = sorted(TASKS, key=lambda t: (MODULES[t[1] - 1][3], t[3]))
    return ordered[:completed_count]


def generate_progress_and_attempts(users):
    progress_rows = []
    attempt_rows = []
    attempt_id = 1

    students = [u for u in users if u[4] == "student"]

    for user in students:
        user_id, client_id = user[0], user[1]
        profile = CLIENT_PROFILES[client_id]
        max_tasks = len(TASKS)
        completed_tasks = int(max_tasks * profile["completion_bias"] * random.uniform(0.5, 1.2))
        completed_tasks = max(0, min(completed_tasks, max_tasks))

        if profile["activity"] < random.random():
            completed_tasks = random.randint(0, 3)

        ordered_tasks = task_list_for_progress(completed_tasks)
        completed_task_ids = {t[0] for t in ordered_tasks}

        modules_seen = set()
        for task in TASKS:
            task_id, module_id = task[0], task[1]
            if task_id in completed_task_ids:
                status = "completed"
                day_offset = task_id * 2 + random.randint(0, 5)
                completed_at = BASE_DATE + timedelta(days=day_offset, hours=random.randint(9, 18))
            elif task_id == (ordered_tasks[-1][0] + 1 if ordered_tasks else 1):
                status = "in_progress"
                completed_at = ""
            else:
                status = "not_started"
                completed_at = ""

            if status != "not_started":
                modules_seen.add(module_id)

            progress_rows.append((
                user_id, module_id, task_id, status,
                completed_at.strftime("%Y-%m-%d %H:%M:%S") if completed_at else "",
            ))

        for module_id in modules_seen:
            module_tasks = [t for t in TASKS if t[1] == module_id]
            all_done = all(t[0] in completed_task_ids for t in module_tasks)
            if all_done:
                progress_rows.append((
                    user_id, module_id, "", "completed",
                    (BASE_DATE + timedelta(days=module_id * 10)).strftime("%Y-%m-%d %H:%M:%S"),
                ))

        if completed_tasks == max_tasks:
            progress_rows.append((
                user_id, 4, "", "completed",
                (BASE_DATE + timedelta(days=75)).strftime("%Y-%m-%d %H:%M:%S"),
            ))

        active_days = max(1, int(completed_tasks * profile["activity"] * random.uniform(0.8, 1.5)))
        for day in range(active_days):
            activity_date = BASE_DATE + timedelta(days=day * 2 + random.randint(0, 1))
            if activity_date > datetime(2026, 5, 1):
                continue

            tasks_today = random.sample(
                list(completed_task_ids) or [1],
                k=min(random.randint(1, 2), len(completed_task_ids) or 1),
            )
            for task_id in tasks_today:
                module_id = next(t[1] for t in TASKS if t[0] == task_id)
                is_hard = task_id in HARD_TASKS
                num_attempts = random.randint(2, 5) if is_hard else random.randint(1, 3)

                for attempt_num in range(1, num_attempts + 1):
                    start = activity_date + timedelta(hours=random.randint(9, 17), minutes=random.randint(0, 59))
                    duration_min = random.randint(8, 45) if is_hard else random.randint(3, 20)
                    finish = start + timedelta(minutes=duration_min)
                    is_success = attempt_num == num_attempts and random.random() > (0.3 if is_hard else 0.1)

                    attempt_rows.append((
                        attempt_id, user_id, task_id,
                        start.strftime("%Y-%m-%d %H:%M:%S"),
                        finish.strftime("%Y-%m-%d %H:%M:%S"),
                        "true" if is_success else "false",
                        attempt_num,
                    ))
                    attempt_id += 1

        if completed_tasks > 0 and random.random() < profile["activity"]:
            stuck_task = min(completed_tasks + 1, max_tasks)
            if stuck_task not in completed_task_ids:
                for attempt_num in range(1, random.randint(3, 6)):
                    start = BASE_DATE + timedelta(days=random.randint(20, 60), hours=random.randint(10, 16))
                    finish = start + timedelta(minutes=random.randint(15, 50))
                    attempt_rows.append((
                        attempt_id, user_id, stuck_task,
                        start.strftime("%Y-%m-%d %H:%M:%S"),
                        finish.strftime("%Y-%m-%d %H:%M:%S"),
                        "false",
                        attempt_num,
                    ))
                    attempt_id += 1

    return progress_rows, attempt_rows


def main():
    print("Generating CSV files...")
    write_csv("clients.csv", ["id", "name", "tariff", "contract_start", "contract_end"], CLIENTS)
    write_csv("modules.csv", ["id", "course_id", "name", "order_num"], MODULES)
    write_csv("tasks.csv", ["id", "module_id", "name", "order_num"], TASKS)

    users = generate_users()
    write_csv(
        "users.csv",
        ["id", "client_id", "full_name", "email", "role", "created_at"],
        users,
    )

    progress, attempts = generate_progress_and_attempts(users)
    write_csv(
        "student_progress.csv",
        ["user_id", "module_id", "task_id", "status", "completed_at"],
        progress,
    )
    write_csv(
        "attempts.csv",
        ["id", "user_id", "task_id", "started_at", "finished_at", "is_success", "attempt_num"],
        attempts,
    )
    print("Done.")


if __name__ == "__main__":
    main()
