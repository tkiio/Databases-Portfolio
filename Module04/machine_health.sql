CREATE VIEW machine_health AS
SELECT s.machine_id, s.metric, MAX(r.value) AS peak, COUNT(*) AS n
FROM sensor AS s JOIN reading AS r USING (sensor_id)
GROUP BY s.machine_id, s.metric;
