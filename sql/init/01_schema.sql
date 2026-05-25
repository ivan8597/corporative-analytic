CREATE DATABASE metabase;
GRANT ALL PRIVILEGES ON DATABASE metabase TO analytics;

\c it_resume_analytics

CREATE TABLE clients (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    tariff          TEXT NOT NULL,
    contract_start  DATE NOT NULL,
    contract_end    DATE NOT NULL
);

CREATE TABLE users (
    id          INTEGER PRIMARY KEY,
    client_id   INTEGER NOT NULL REFERENCES clients (id),
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('student', 'curator', 'admin')),
    created_at  TIMESTAMP NOT NULL
);

CREATE TABLE modules (
    id          INTEGER PRIMARY KEY,
    course_id   INTEGER NOT NULL,
    name        TEXT NOT NULL,
    order_num   INTEGER NOT NULL
);

CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY,
    module_id   INTEGER NOT NULL REFERENCES modules (id),
    name        TEXT NOT NULL,
    order_num   INTEGER NOT NULL
);

CREATE TABLE student_progress (
    user_id       INTEGER NOT NULL REFERENCES users (id),
    module_id     INTEGER NOT NULL REFERENCES modules (id),
    task_id       INTEGER REFERENCES tasks (id),
    status        TEXT NOT NULL CHECK (status IN ('not_started', 'in_progress', 'completed')),
    completed_at  TIMESTAMP
);

CREATE TABLE attempts (
    id           INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users (id),
    task_id      INTEGER NOT NULL REFERENCES tasks (id),
    started_at   TIMESTAMP NOT NULL,
    finished_at  TIMESTAMP,
    is_success   BOOLEAN NOT NULL DEFAULT FALSE,
    attempt_num  INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_users_client_id ON users (client_id);
CREATE INDEX idx_attempts_user_started ON attempts (user_id, started_at);
CREATE INDEX idx_attempts_task_id ON attempts (task_id);
CREATE INDEX idx_student_progress_user_id ON student_progress (user_id);
CREATE INDEX idx_tasks_module_id ON tasks (module_id);
