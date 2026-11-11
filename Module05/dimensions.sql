-- Separate wider copy: leave the main four-table experiment reproducible.
DROP TABLE IF EXISTS report_jobpart_wide;
DROP TABLE IF EXISTS vendor;
DROP TABLE IF EXISTS site_dim;
CREATE TABLE vendor(part_no TEXT NOT NULL PRIMARY KEY, vendor TEXT NOT NULL, country TEXT NOT NULL);
INSERT INTO vendor
SELECT part_no, 'vendor-' || (rowid % 12),
       CASE rowid % 3 WHEN 0 THEN 'DE' WHEN 1 THEN 'CN' ELSE 'US' END
FROM part;

CREATE TABLE site_dim(site TEXT NOT NULL PRIMARY KEY, region TEXT NOT NULL, manager TEXT NOT NULL);
INSERT INTO site_dim
SELECT site, 'region-' || (row_number() OVER (ORDER BY site) % 5),
       'mgr-' || row_number() OVER (ORDER BY site)
FROM (SELECT DISTINCT site FROM machine);

CREATE TABLE report_jobpart_wide AS
SELECT j.job_id, m.machine_id, m.site, sd.region, j.technician, jp.part_no,
       p.part_price, v.vendor, j.done_on
FROM job AS j
JOIN machine AS m ON m.machine_id = j.machine_id
JOIN site_dim AS sd ON sd.site = m.site
JOIN job_part AS jp ON jp.job_id = j.job_id
JOIN part AS p ON p.part_no = jp.part_no
JOIN vendor AS v ON v.part_no = p.part_no;
