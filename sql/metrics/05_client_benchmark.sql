-- Метрика 5: Бенчмарк клиентов по completion rate
-- Визуализация: Bar chart с выделением целевого клиента
-- Metabase variable: {{client_id}}

WITH client_completion AS (
    SELECT
        u.client_id,
        c.name AS client_name,
        COUNT(DISTINCT u.id) AS total_students,
        COUNT(DISTINCT CASE
            WHEN sp.status = 'completed'
             AND sp.task_id IS NULL
             AND sp.module_id = 4
            THEN u.id
        END) AS completed_course,
        ROUND(
            100.0 * COUNT(DISTINCT CASE
                WHEN sp.status = 'completed'
                 AND sp.task_id IS NULL
                 AND sp.module_id = 4
                THEN u.id
            END) / NULLIF(COUNT(DISTINCT u.id), 0),
            1
        ) AS completion_rate_pct
    FROM users u
    JOIN clients c ON c.id = u.client_id
    LEFT JOIN student_progress sp ON sp.user_id = u.id
    WHERE u.role = 'student'
    GROUP BY u.client_id, c.name
    HAVING COUNT(DISTINCT u.id) >= 3
)
SELECT
    client_name,
    client_id,
    total_students,
    completed_course,
    completion_rate_pct,
    CASE WHEN client_id = {{client_id}} THEN TRUE ELSE FALSE END AS is_target_client
FROM client_completion
ORDER BY completion_rate_pct DESC;
