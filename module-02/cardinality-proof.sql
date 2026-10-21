PRAGMA foreign_keys = ON;
CREATE TABLE Machine (
    machine_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE Sensor (
    sensor_id INTEGER PRIMARY KEY,
    sensor_type TEXT NOT NULL,
    machine_id INTEGER NOT NULL REFERENCES Machine(machine_id)
);
INSERT INTO Machine (machine_id, name) VALUES (1, 'CNC-01');
INSERT INTO Sensor (sensor_id, sensor_type, machine_id)
VALUES (101, 'temperature', 1), (102, 'vibration', 1);
.headers on
.mode column
SELECT Machine.name, COUNT(Sensor.sensor_id) AS sensor_count
FROM Machine
JOIN Sensor ON Sensor.machine_id = Machine.machine_id
GROUP BY Machine.machine_id;
