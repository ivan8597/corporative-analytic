# IT Resume — Corporate Client Analytics

Локальный стенд для практики построения дашборда корпоративного клиента (client_id = 1).

## Установка и запуск с GitHub

### Требования

Перед установкой убедитесь, что установлены:

| Инструмент | Минимальная версия | Проверка |
|------------|-------------------|----------|
| [Git](https://git-scm.com/) | любая актуальная | `git --version` |
| [Docker](https://www.docker.com/) | 20.10+ | `docker --version` |
| [Docker Compose](https://docs.docker.com/compose/) | v2+ | `docker compose version` |
| [Python](https://www.python.org/) | 3.9+ | `python3 --version` |

> Docker Desktop (macOS / Windows) включает Docker и Compose. На Linux установите `docker.io` и `docker-compose-plugin`.

### 1. Клонирование репозитория

```bash
git clone https://github.com/ivan8597/corporative-analytic.git
cd corporative-analytic
```

**Альтернатива — скачать ZIP:**

1. Откройте страницу репозитория на GitHub.
2. **Code** → **Download ZIP**.
3. Распакуйте архив и перейдите в папку проекта:

```bash
cd corporative-analytic
```

### 2. Подготовка данных (если папка `data/` пустая)

CSV-файлы уже могут быть в репозитории. Если их нет — сгенерируйте:

```bash
python3 scripts/generate_data.py
```

### 3. Запуск контейнеров

```bash
docker compose up -d
```

Дождитесь готовности сервисов (1–3 минуты при первом запуске):

```bash
docker compose ps
```

Ожидаемый статус: `postgres` — **healthy**, `metabase` — **Up**.

Проверка Metabase:

```bash
curl http://localhost:3000/api/health
```

В ответе должно быть `"status":"ok"`.

### 4. Настройка дашборда Metabase

```bash
python3 scripts/setup_metabase.py
```

Скрипт автоматически:
- создаёт учётную запись администратора;
- подключает PostgreSQL;
- создаёт 5 SQL-вопросов и дашборд;
- добавляет блоки «Выводы → Рекомендации».

Если дашборд уже был создан ранее, для обновления только текстовых блоков:

```bash
python3 scripts/update_dashboard_insights.py
```

### 5. Открыть приложение

| Что открыть | Адрес |
|-------------|-------|
| Дашборд | http://localhost:3000/dashboard/1 |
| Metabase (главная) | http://localhost:3000 |

**Учётные данные Metabase:**

- Email: `admin@it-resume.local`
- Пароль: `Analytics2025!`

### Остановка и удаление

```bash
# Остановить контейнеры
docker compose down

# Остановить и удалить данные БД (полный сброс)
docker compose down -v
```

После `down -v` при следующем запуске данные PostgreSQL создаются заново из CSV.



### Частые проблемы

| Проблема | Решение |
|----------|---------|
| Порт 5432 или 3000 занят | Остановите другие сервисы или измените порты в `docker-compose.yml` |
| Metabase отвечает 503 | Подождите 2–3 мин, затем повторите `setup_metabase.py` |
| `setup_metabase.py` падает с ошибкой сети | Убедитесь, что `docker compose ps` показывает оба контейнера **Up** |
| Пустой дашборд | Запустите `python3 scripts/generate_data.py`, затем `docker compose down -v && docker compose up -d` |

---

## Быстрый старт (если проект уже склонирован)

```bash
docker compose up -d
python3 scripts/setup_metabase.py              # вопросы, дашборд, выводы
python3 scripts/update_dashboard_insights.py   # только обновить текстовые блоки
```

| Сервис     | URL / адрес              | Логин / пароль      |
|------------|--------------------------|---------------------|
| Metabase   | http://localhost:3000/dashboard/1 | admin@it-resume.local / Analytics2025! |
| PostgreSQL | localhost:5432           | analytics / analytics |
| База данных | it_resume_analytics     | —                   |

### Автоматическая настройка Metabase

Скрипт `scripts/setup_metabase.py`:
- создаёт admin-аккаунт (если Metabase ещё не настроен);
- подключает PostgreSQL;
- создаёт 5 SQL-вопросов из `sql/metrics/`;
- собирает дашборд с фильтрами `client_id`, `date_from`, `date_to`;
- добавляет текстовые блоки **«Выводы → Рекомендации»** под каждым графиком.

После запуска откройте http://localhost:3000/dashboard/1

**Вручную (опционально):**
- Dashboard → ⋮ → Edit → Auto-refresh → 1 hour
- В таблице «Индивидуальный прогресс» → Conditional formatting для `progress_pct`

### Ручная настройка Metabase (если скрипт не используется)

1. Откройте http://localhost:3000 и создайте аккаунт администратора.
2. **Add database** → PostgreSQL:
   - Host: `postgres`
   - Port: `5432`
   - Database: `it_resume_analytics`
   - Username / Password: `analytics` / `analytics`
3. Создайте вопросы из SQL-файлов в `sql/metrics/`.
4. Соберите дашборд с фильтрами `client_id` (default: 1), `date_from`, `date_to`.
5. Запустите `python3 scripts/update_dashboard_insights.py` для текстовых блоков.



## Перегенерация данных

```bash
python3 scripts/generate_data.py
docker compose down -v
docker compose up -d
```

> `-v` удаляет volume Postgres — данные пересоздаются из CSV заново.

## Таблицы

| Таблица           | Описание                          |
|-------------------|-----------------------------------|
| clients           | Корпоративные заказчики           |
| users             | Студенты и кураторы               |
| modules           | Модули курса                      |
| tasks             | Задачи внутри модулей             |
| student_progress  | Прогресс по задачам и модулям     |
| attempts          | Попытки решения задач             |

## Метрики (sql/metrics/)

1. `01_daily_activity.sql` — ежедневная активность (Line chart)
2. `02_course_funnel.sql` — воронка курса (Funnel)
3. `03_task_difficulty.sql` — сложность задач (Bar + Table)
4. `04_student_progress.sql` — прогресс студентов (Table)
5. `05_client_benchmark.sql` — бенчмарк клиентов (Bar)

---


