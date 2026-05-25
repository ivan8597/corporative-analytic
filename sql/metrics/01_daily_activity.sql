-- Метрика 1: Ежедневная активность студентов
-- Визуализация: Line chart
-- Metabase variables: {{client_id}}, {{date_from}}, {{date_to}}

SELECT
    DATE(a.started_at) AS activity_date,
    COUNT(DISTINCT a.user_id) AS active_students
FROM attempts a
JOIN users u ON u.id = a.user_id
WHERE u.client_id = {{client_id}}
  AND u.role = 'student'
  AND a.started_at >= {{date_from}}::timestamp
  AND a.started_at < {{date_to}}::timestamp + INTERVAL '1 day'
GROUP BY 1
ORDER BY 1;
