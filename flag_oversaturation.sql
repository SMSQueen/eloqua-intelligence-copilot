-- models/sql/flag_oversaturation.sql
WITH w AS (
  SELECT
    DATE(date) AS activity_date,
    segment_id,
    sends,
    opens,
    clicks,
    unique_contacts_reached,
    sends / NULLIF(unique_contacts_reached, 0) AS EPC
  FROM emails_by_segment_daily
),
roll AS (
  SELECT
    segment_id,
    activity_date,
    AVG(EPC) OVER (PARTITION BY segment_id ORDER BY activity_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS EPC_7d,
    AVG(clicks) OVER (PARTITION BY segment_id ORDER BY activity_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) /
    NULLIF(AVG(opens) OVER (PARTITION BY segment_id ORDER BY activity_date
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 0) AS ctor_7d
  FROM w
)
SELECT
  r.segment_id,
  r.activity_date,
  r.EPC_7d,
  r.ctor_7d,
  CASE WHEN r.EPC_7d > 4 AND r.ctor_7d < (b.baseline_ctor - 1.5 * b.baseline_sigma)
       THEN TRUE ELSE FALSE END AS oversaturation_flag
FROM roll r
JOIN (
  SELECT segment_id,
         AVG(ctor_7d) AS baseline_ctor,
         STDDEV_SAMP(ctor_7d) AS baseline_sigma
  FROM roll
  GROUP BY 1
) b USING (segment_id);
