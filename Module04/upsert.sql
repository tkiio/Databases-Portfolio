-- Run once after setup.sql. The key identifies the SAME sensor and timestamp.
CREATE UNIQUE INDEX IF NOT EXISTS ux_reading_sensor_ts
ON reading(sensor_id, ts);

INSERT INTO reading(sensor_id, ts, value, interval_s)
VALUES (1, '2026-03-01 08:00:00', 41.7, 1)
ON CONFLICT(sensor_id, ts) DO UPDATE SET value = excluded.value;

SELECT sensor_id, ts, value FROM reading WHERE sensor_id = 1;
SELECT COUNT(*) AS rows_for_key FROM reading
WHERE sensor_id = 1 AND ts = '2026-03-01 08:00:00';
