PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE reading(machine TEXT, vib REAL);
INSERT INTO reading VALUES('cnc-01',1.2),
  ('cnc-02',2.4),
  ('cnc-01',0.9);
COMMIT;
