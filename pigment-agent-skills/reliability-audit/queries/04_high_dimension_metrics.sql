-- High-dimension metrics (nb_dims > 6 by default)
-- Source equivalent: 13-performance-data-analysis.md "High-Dimension Metrics"

SELECT DISTINCT
  metric_name,
  nb_dims,
  execution_time
FROM
  `your_project.your_dataset.executions_table`
WHERE
  nb_dims > 6
ORDER BY
  nb_dims DESC,
  execution_time DESC;
