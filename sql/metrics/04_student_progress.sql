-- Метрика 4: Индивидуальный прогресс студентов
-- Визуализация: Table с conditional formatting
-- Metabase variable: {{client_id}}

WITH totals AS (
    SELECT COUNT(*) AS total_tasks FROM tasks
),
student_stats AS (
    SELECT
        u.id AS user_id,
        u.full_name,
        u.email,
        COUNT(DISTINCT CASE
            WHEN sp.status = 'completed' AND sp.task_id IS NOT NULL THEN sp.task_id
        END) AS completed_tasks,
        MAX(a.started_at) AS last_activity_at,
        COUNT(DISTINCT DATE(a.started_at)) AS active_days
    FROM users u
    LEFT JOIN student_progress sp ON sp.user_id = u.id
    LEFT JOIN attempts a ON a.user_id = u.id
    WHERE u.client_id = {{client_id}}
      AND u.role = 'student'
    GROUP BY u.id, u.full_name, u.email
)
SELECT
    s.full_name,
    s.email,
    s.completed_tasks,
    t.total_tasks,
    ROUND(100.0 * s.completed_tasks / NULLIF(t.total_tasks, 0), 1) AS progress_pct,
    s.active_days,
    s.last_activity_at,
    CASE
        WHEN 100.0 * s.completed_tasks / NULLIF(t.total_tasks, 0) >= 80 THEN 'Готов'
        WHEN s.last_activity_at IS NULL
          OR s.last_activity_at < NOW() - INTERVAL '14 days' THEN 'Отстаёт'
        WHEN 100.0 * s.completed_tasks / NULLIF(t.total_tasks, 0) >= 40 THEN 'В процессе'
        ELSE 'Начал'
    END AS status_label
FROM student_stats s
CROSS JOIN totals t
ORDER BY progress_pct ASC, last_activity_at ASC NULLS FIRST;
