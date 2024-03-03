-- TODO: Credentials to database
.open credentials.db
DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users(
    id                  TEXT PRIMARY KEY     NOT NULL,
    username            TEXT UNIQUE          NOT NULL,
    login_hash          TEXT                 NOT NULL
);
INSERT INTO users(id, username, login_hash)
VALUES ("9e5d0a6c-16c8-43bd-861e-91296e94ffa9", "test", "test_hash");
