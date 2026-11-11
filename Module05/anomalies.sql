-- Module 5, Round 2. Each SAVEPOINT restores the original five rows afterwards.
-- This table deliberately has no key, NOT NULL or other integrity constraints.
DROP TABLE IF EXISTS flat5;
CREATE TABLE flat5(
    job_id INTEGER, machine_id TEXT, site TEXT,
    technician TEXT, part_no TEXT, part_price REAL
);
INSERT INTO flat5 VALUES
  (1,'cnc-01','Gütersloh','tech-0','P-0001',6.00),
  (1,'cnc-01','Gütersloh','tech-0','P-0002',7.00),
  (2,'cnc-02','Gütersloh','tech-1','P-0001',6.00),
  (2,'cnc-02','Gütersloh','tech-1','P-0003',8.50),
  (3,'cnc-01','Gütersloh','tech-0','P-0003',8.50);
SELECT COUNT(*) AS baseline_rows FROM flat5;

-- Case 1: changing one machine fact requires updating THREE fact rows.
SAVEPOINT full_site_update;
UPDATE flat5 SET site='Bielefeld' WHERE machine_id='cnc-01';
SELECT changes() AS touched_site_rows;
SELECT job_id, machine_id, part_no, site FROM flat5 WHERE machine_id='cnc-01';
ROLLBACK TO full_site_update;
RELEASE full_site_update;

-- The update anomaly: editing only one copy leaves inconsistent sites.
SAVEPOINT partial_site_update;
UPDATE flat5 SET site='Bielefeld' WHERE job_id=1 AND part_no='P-0001';
SELECT job_id, machine_id, part_no, site FROM flat5 WHERE machine_id='cnc-01';
SELECT COUNT(*) AS inconsistent_machines FROM (
    SELECT machine_id FROM flat5
    GROUP BY machine_id HAVING COUNT(DISTINCT site)>1
);
ROLLBACK TO partial_site_update;
RELEASE partial_site_update;

-- Case 2: the unused part is accepted only as a row with no job/machine.
-- There is no SQL error here: the schema allows NULL. The problem is that
-- this row no longer describes an actual part used by an actual job.
SAVEPOINT unused_part;
INSERT INTO flat5(job_id,machine_id,site,technician,part_no,part_price)
VALUES (NULL,NULL,NULL,NULL,'P-0004',9.00);
SELECT * FROM flat5 WHERE part_no='P-0004';
SELECT COUNT(*) AS unused_part_placeholder_rows FROM flat5
WHERE part_no='P-0004' AND job_id IS NULL AND machine_id IS NULL;
ROLLBACK TO unused_part;
RELEASE unused_part;

-- Case 3: job 1 is the last/only job using P-0002. Removing that job also
-- removes the only stored fact that P-0002 exists and costs 7.00.
SAVEPOINT delete_last_use;
DELETE FROM flat5 WHERE job_id=1;
SELECT changes() AS removed_job1_rows;
SELECT COUNT(*) AS retained_part2_rows FROM flat5 WHERE part_no='P-0002';
SELECT * FROM flat5 ORDER BY job_id,part_no;
ROLLBACK TO delete_last_use;
RELEASE delete_last_use;

SELECT COUNT(*) AS restored_rows FROM flat5;
