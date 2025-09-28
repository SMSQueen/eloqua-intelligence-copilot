-- models/sql/rolling_14d.sql
WITH base AS (
  SELECT
    DATE(date) AS activity_date,
    segment_id,
    SUM(sends) AS sends,
    SUM(opens) AS opens,
    SUM(clicks) AS clicks,
    SUM(unsubs) AS unsubs,
    SUM(spam_complaints) AS spam,
    SUM(unique_contacts_reached) AS contacts
  FROM emails_by_segment_daily
  GROUP BY 1,2
),
roll AS (
  SELECT
    segment_id,
    activity_date,
    SUM(sends) OVER (PARTITION BY segment_id ORDER BY activity_date
      ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS sends_14d,
    SUM(opens) OVER (PARTITION BY segment_id ORDER BY activity_date
      ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS opens_14d,
    SUM(clicks) OVER (PARTITION BY segment_id ORDER BY activity_date
      ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS clicks_14d
  FROM base
)
SELECT
  segment_id,
  activity_date,
  sends_14d,
  opens_14d,
  clicks_14d,
  SAFE_DIVIDE(clicks_14d, NULLIF(opens_14d,0)) AS ctor_14d
FROM roll;
