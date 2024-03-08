-- TODO: Credentials to database
DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users(
    id                          TEXT PRIMARY KEY     NOT NULL,
    username                    TEXT UNIQUE          NOT NULL,
    login_hash                  TEXT                 NOT NULL,
    front_login_salt            TEXT                 NOT NULL,
    encryption_salt             TEXT                 NOT NULL,
    encrypted_encryption_key    TEXT                 NOT NULL,
    password_change_time        INTEGER              NOT NULL
);
INSERT INTO users(
    id,
    username,
    login_hash,
    front_login_salt,
    encryption_salt,
    encrypted_encryption_key,
    password_change_time
)
VALUES (
    '9e5d0a6c-16c8-43bd-861e-91296e94ffa9',
    'test',
    '$argon2id$v=19$m=65536,t=3,p=4$PmMiESMu13n+0O8TzlIrxg$QwnIqsJ/qZEW51dcHpw5x4SFVJt63aQr03jFH66qyB8',
    '$2a$10$rqjuEeu.VVLESZi07oYpTe',
    '$2a$10$iLz9ZEVEeGivdxwRskk8Lu',
    'U2FsdGVkX18PwKtunh9PlsCBvq7NhhaziGFG4pCnfW3ScguCVowwuG4ok+ssK7va4JjviIjgVGW26UIUsdvLwZMbfitCu1SSEtLiEt13mp5z6GWhmkClFz9noIgZ8uwJ',
    1709459026
);

DROP TABLE IF EXISTS tokens;
CREATE TABLE IF NOT EXISTS tokens(
    token                   TEXT PRIMARY KEY     NOT NULL,
    user_id                 TEXT                 NOT NULL,
    created_at              INTEGER              NOT NULL,
    FOREIGN KEY(user_id)    REFERENCES users(id)
);
