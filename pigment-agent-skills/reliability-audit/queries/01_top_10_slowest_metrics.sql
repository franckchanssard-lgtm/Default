-- Top 10 slowest metric executions
-- Source equivalent: 13-performance-data-analysis.md "Top 10 Slowest Metrics"

SELECT
  application,
  metric_name,
  execution_time,
  computed_rows,
  nb_dims,
  scoped_level
FROM
  `your_project.your_dataset.executions_table`
ORDER BY
  execution_time DESC
LIMIT 10;
