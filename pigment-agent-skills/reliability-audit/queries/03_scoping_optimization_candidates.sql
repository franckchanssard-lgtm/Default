-- Scoping optimization candidates:
-- unscoped (NoChange) metric executions with high average runtime
-- Source equivalent: 13-performance-data-analysis.md "Scoping Optimization Opportunities"

-- Adjust threshold as needed (milliseconds)
-- WHERE execution_time > 5000

SELECT
  metric_name,
  COUNT(*) AS execution_count,
  AVG(execution_time) AS avg_execution_time_ms,
  MAX(execution_time) AS max_execution_time_ms,
  SUM(execution_time) AS total_execution_time_ms
FROM
  `your_project.your_dataset.executions_table`
WHERE
  scoped_level = 'NoChange'
  AND execution_time > 5000
GROUP BY
  metric_name
ORDER BY
  avg_execution_time_ms DESC;
