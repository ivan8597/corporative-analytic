-- Метрика 2: Воронка прохождения курса
-- Визуализация: Funnel chart
-- Metabase variable: {{client_id}}

WITH client_students AS (
    SELECT id AS user_id
    FROM users
    WHERE client_id = {{client_id}}
      AND role = 'student'
),
module1_tasks AS (
    SELECT id FROM tasks WHERE module_id = 1
),
all_tasks AS (
    SELECT id FROM tasks
),
funnel AS (
    SELECT 'Зарегистрированы' AS stage, 1 AS stage_order, COUNT(*) AS students
    FROM client_students

    UNION ALL

    SELECT 'Начали обучение', 2, COUNT(DISTINCT a.user_id)
    FROM attempts a
    JOIN client_students cs ON cs.user_id = a.user_id

    UNION ALL

    SELECT 'Завершили модуль 1 (Python)', 3, COUNT(DISTINCT sp.user_id)
    FROM student_progress sp
    JOIN client_students cs ON cs.user_id = sp.user_id
    WHERE sp.module_id = 1
      AND sp.task_id IS NULL
      AND sp.status = 'completed'

    UNION ALL

    SELECT 'Завершили модуль 2 (SQL)', 4, COUNT(DISTINCT sp.user_id)
    FROM student_progress sp
    JOIN client_students cs ON cs.user_id = sp.user_id
    WHERE sp.module_id = 2
      AND sp.task_id IS NULL
      AND sp.status = 'completed'

    UNION ALL

    SELECT 'Завершили курс', 5, COUNT(DISTINCT sp.user_id)
    FROM student_progress sp
    JOIN client_students cs ON cs.user_id = sp.user_id
    WHERE sp.module_id = 4
      AND sp.task_id IS NULL
      AND sp.status = 'completed'
)
SELECT
    stage,
    students,
    ROUND(
        100.0 * students / NULLIF(FIRST_VALUE(students) OVER (ORDER BY stage_order), 0),
        1
    ) AS conversion_pct
FROM funnel
ORDER BY stage_order;
