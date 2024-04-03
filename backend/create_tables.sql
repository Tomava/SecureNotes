DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users(
    id                          TEXT PRIMARY KEY     NOT NULL,
    username                    VARCHAR(20) UNIQUE   NOT NULL,
    login_hash                  CHAR(97)             NOT NULL,
    front_login_salt            CHAR(29)             NOT NULL,
    encryption_salt             CHAR(29)             NOT NULL,
    encrypted_encryption_key    CHAR(128)            NOT NULL,
    password_change_time        INTEGER              NOT NULL,
    otp_code                    CHAR(32)
);
-- INSERT INTO users(
--     id,
--     username,
--     login_hash,
--     front_login_salt,
--     encryption_salt,
--     encrypted_encryption_key,
--     password_change_time
-- )

-- VALUES (
--     '9e5d0a6c-16c8-43bd-861e-91296e94ffa9',
--     'test',
--     '$argon2id$v=19$m=65536,t=3,p=4$PmMiESMu13n+0O8TzlIrxg$QwnIqsJ/qZEW51dcHpw5x4SFVJt63aQr03jFH66qyB8',
--     '$2a$10$rqjuEeu.VVLESZi07oYpTe',
--     '$2a$10$iLz9ZEVEeGivdxwRskk8Lu',
--     'U2FsdGVkX18PwKtunh9PlsCBvq7NhhaziGFG4pCnfW3ScguCVowwuG4ok+ssK7va4JjviIjgVGW26UIUsdvLwZMbfitCu1SSEtLiEt13mp5z6GWhmkClFz9noIgZ8uwJ',
--     1709459026
-- );

DROP TABLE IF EXISTS tokens;
CREATE TABLE IF NOT EXISTS tokens(
    token                   CHAR(128) PRIMARY KEY   NOT NULL,
    user_id                 TEXT                    NOT NULL,
    created_at              INTEGER                 NOT NULL,
    FOREIGN KEY(user_id)    REFERENCES users(id)
);

DROP TABLE IF EXISTS notes;
CREATE TABLE IF NOT EXISTS notes(
    note_id                 TEXT PRIMARY KEY     NOT NULL,
    owner_id                TEXT                 NOT NULL,
    created_at              INTEGER              NOT NULL,
    modified_at             INTEGER              NOT NULL,
    note_title              BYTEA,
    note_body               BYTEA,
    FOREIGN KEY(owner_id)   REFERENCES users(id)
);

-- INSERT INTO notes(
--     note_id,
--     owner_id,
--     created_at,
--     modified_at,
--     note_data
-- )
-- VALUES (
--     'b1e0d193-1fc2-422a-9761-f20518b3ba6e',
--     '9e5d0a6c-16c8-43bd-861e-91296e94ffa9',
--     1710159005,
--     1710159005,
--     E'\\xCDCDCDCD'
-- );

-- INSERT INTO notes(
--     note_id,
--     owner_id,
--     created_at,
--     modified_at,
--     note_data
-- )
-- VALUES (
--     '8f6926ca-59ed-4116-a8ab-b212448bec16',
--     '9e5d0a6c-16c8-43bd-861e-91296e94ffa9',
--     1710159168,
--     1710159168,
--     E'\\xDCDCDCDC'
-- );