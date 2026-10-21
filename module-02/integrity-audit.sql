.headers on
.mode column
.timer on

-- Defect 1: orphan maintenance jobs (machine_name not in machine)
SELECT m.job_id, m.machine_name
FROM maint_job m
LEFT JOIN machine x ON m.machine_name = x.machine_name
WHERE x.machine_name IS NULL;

-- Defect 2: duplicate natural keys in part
SELECT part_no, COUNT(*) AS copies
FROM part GROUP BY part_no HAVING COUNT(*) > 1;

-- Defect 3: text ordering, not numeric comparison
SELECT part_no, unit_price FROM part WHERE unit_price < '15';
-- Numeric comparison for contrast
SELECT part_no, unit_price FROM part WHERE CAST(unit_price AS NUMERIC) < 15;

-- Defect 4: installed values not shaped like YYYY-MM-DD
SELECT machine_name, installed FROM machine
WHERE installed NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]';

-- Defect 5: joining the list as though it were one part key
SELECT j.job_id, p.description
FROM maint_job j
JOIN part p ON p.part_no = j.parts_used;
