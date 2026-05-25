-- Метрика 3: Сложность задач — время и попытки
-- Визуализация: Bar chart + Table
-- Metabase variables: {{client_id}}, {{date_from}}, {{date_to}}

SELECT
    m.name AS module_name,
    t.name AS task_name,
    COUNT(DISTINCT a.user_id) AS students_attempted,
    ROUND(AVG(EXTRACT(EPOCH FROM (a.finished_at - a.started_at)) / 60), 1) AS avg_minutes,
    ROUND(AVG(a.attempt_num), 1) AS avg_attempts,
    ROUND(
        100.0 * SUM(CASE WHEN a.is_success THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
        1
    ) AS success_rate_pct
FROM attempts a
JOIN users u ON u.id = a.user_id
JOIN tasks t ON t.id = a.task_id
JOIN modules m ON m.id = t.module_id
WHERE u.client_id = {{client_id}}
  AND u.role = 'student'
  AND a.finished_at IS NOT NULL
  AND a.started_at >= {{date_from}}::timestamp
  AND a.started_at < {{date_to}}::timestamp + INTERVAL '1 day'
GROUP BY m.name, m.order_num, t.name, t.order_num
HAVING COUNT(DISTINCT a.user_id) >= 2
ORDER BY m.order_num, t.order_num, avg_attempts DESC;
