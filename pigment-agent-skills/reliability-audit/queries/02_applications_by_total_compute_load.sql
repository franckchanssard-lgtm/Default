-- Applications by total compute load
-- Source equivalent: 13-performance-data-analysis.md "Applications by Total Compute Load"

SELECT
  application,
  SUM(execution_time) AS total_execution_time_ms,
  COUNT(*) AS execution_count,
  AVG(execution_time) AS avg_execution_time_ms
FROM
  `your_project.your_dataset.executions_table`
GROUP BY
  application
ORDER BY
  total_execution_time_ms DESC;
