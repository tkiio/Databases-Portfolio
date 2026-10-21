.headers on
.mode column
.timer on

-- Observed jobs per machine name (includes the orphan cnc-05).
SELECT machine_name, COUNT(*) AS job_count
FROM maint_job
GROUP BY machine_name
ORDER BY machine_name;

-- Observed jobs per technician.
SELECT technician, COUNT(*) AS job_count
FROM maint_job
GROUP BY technician
ORDER BY technician;

-- Count list entries safely: NULL means no parts were recorded.
SELECT job_id,
       parts_used,
       CASE WHEN parts_used IS NULL THEN 0
            ELSE LENGTH(parts_used) - LENGTH(REPLACE(parts_used, ',', '')) + 1
       END AS n_parts
FROM maint_job
ORDER BY job_id;

-- Number of jobs whose list contains multiple part numbers.
SELECT COUNT(*) AS jobs_with_multiple_parts
FROM maint_job
WHERE parts_used IS NOT NULL
  AND LENGTH(parts_used) - LENGTH(REPLACE(parts_used, ',', '')) >= 1;
