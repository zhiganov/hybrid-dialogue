CREATE TABLE IF NOT EXISTS rooms (
  id                  TEXT PRIMARY KEY,
  node_title          TEXT NOT NULL,
  node_description    TEXT NOT NULL,
  facilitation_prompt TEXT NOT NULL,
  facilitator_token   TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS participants (
  id           TEXT PRIMARY KEY,
  room_id      TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  token        TEXT NOT NULL,
  joined_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS participants_room_idx ON participants(room_id);

CREATE TABLE IF NOT EXISTS messages (
  id              BIGSERIAL PRIMARY KEY,
  room_id         TEXT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  author_type     TEXT NOT NULL CHECK (author_type IN ('human','claude','system')),
  participant_id  TEXT REFERENCES participants(id) ON DELETE SET NULL,
  body            TEXT NOT NULL,
  contribution_tag TEXT CHECK (contribution_tag IN ('question','story','challenge','synthesis')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_room_id_idx ON messages(room_id, id);

CREATE TABLE IF NOT EXISTS harvests (
  id           BIGSERIAL PRIMARY KEY,
  room_id      TEXT NOT NULL UNIQUE REFERENCES rooms(id) ON DELETE CASCADE,
  body         TEXT NOT NULL,
  finalized_at TIMESTAMPTZ
);
