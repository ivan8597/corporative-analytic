\c it_resume_analytics

COPY clients FROM '/data/clients.csv' WITH (FORMAT csv, HEADER true);
COPY users FROM '/data/users.csv' WITH (FORMAT csv, HEADER true);
COPY modules FROM '/data/modules.csv' WITH (FORMAT csv, HEADER true);
COPY tasks FROM '/data/tasks.csv' WITH (FORMAT csv, HEADER true);
COPY student_progress FROM '/data/student_progress.csv' WITH (FORMAT csv, HEADER true);
COPY attempts FROM '/data/attempts.csv' WITH (FORMAT csv, HEADER true);
