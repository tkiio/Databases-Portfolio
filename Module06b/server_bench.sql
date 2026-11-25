-- Module 6b: manual PostgreSQL row-lock worksheet.
-- Run selected sections in the indicated pgweb connection, not the whole file.
-- The demo table already exists. No credentials or server setup are included.

-- 1. Run in each connection separately: confirm different backend IDs.
SELECT pg_backend_pid() AS backend_pid;

-- 2. Connection A: begin, then update; leave the transaction open.
BEGIN;
UPDATE module06b_server_demo
SET status = 'running', updated_by = 'connection-A'
WHERE id = 1
RETURNING pg_backend_pid() AS backend_pid, id, status, updated_by;

-- 3. Connection B: this waits while A holds the row lock.
UPDATE module06b_server_demo
SET status = 'inspection', updated_by = 'connection-B'
WHERE id = 1
RETURNING pg_backend_pid() AS backend_pid, id, status, updated_by;

-- 4. Connection A: inspect the blocking relationship before committing.
-- These were the observed IDs on 2026-11-19. Replace them with the actual
-- IDs from step 1 when repeating the test with new connections.
SELECT pid, state, wait_event_type, wait_event,
       pg_blocking_pids(pid) AS blocked_by
FROM pg_stat_activity
WHERE datname = current_database() AND pid IN (33694, 33673)
ORDER BY pid;

-- 5. Connection A: release the lock; B can now finish.
COMMIT;

-- 6. Connection B: inspect the final committed result.
SELECT pg_backend_pid() AS backend_pid, id, status, updated_by
FROM module06b_server_demo
WHERE id = 1;
