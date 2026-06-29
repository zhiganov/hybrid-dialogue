import { query } from "./db";
import { generateToken, type ContributionTag } from "./domain";

export type AuthorType = "human" | "claude" | "system";

export type Room = {
  id: string;
  nodeTitle: string;
  nodeDescription: string;
  facilitationPrompt: string;
  facilitatorToken: string;
  listed: boolean;
  createdAt: string;
};
export type Participant = {
  id: string;
  roomId: string;
  displayName: string;
  token: string;
  joinedAt: string;
};
export type Message = {
  id: number;
  roomId: string;
  authorType: AuthorType;
  participantId: string | null;
  authorName: string | null;
  body: string;
  contributionTag: ContributionTag | null;
  createdAt: string;
};
export type Harvest = {
  id: number;
  roomId: string;
  body: string;
  finalizedAt: string | null;
};

type RoomRow = {
  id: string;
  node_title: string;
  node_description: string;
  facilitation_prompt: string;
  facilitator_token: string;
  listed: boolean;
  created_at: string;
};
const toRoom = (r: RoomRow): Room => ({
  id: r.id,
  nodeTitle: r.node_title,
  nodeDescription: r.node_description,
  facilitationPrompt: r.facilitation_prompt,
  facilitatorToken: r.facilitator_token,
  listed: r.listed,
  createdAt: r.created_at,
});

export async function createRoom(input: {
  nodeTitle: string;
  nodeDescription: string;
  facilitationPrompt: string;
  listed?: boolean;
}): Promise<Room> {
  const id = generateToken();
  const facilitatorToken = generateToken();
  const rows = await query<RoomRow>(
    `INSERT INTO rooms (id, node_title, node_description, facilitation_prompt, facilitator_token, listed)
     VALUES ($1,$2,$3,$4,$5,$6) RETURNING *`,
    [id, input.nodeTitle, input.nodeDescription, input.facilitationPrompt, facilitatorToken, input.listed ?? true]
  );
  return toRoom(rows[0]);
}

export async function getRoom(id: string): Promise<Room | null> {
  const rows = await query<RoomRow>("SELECT * FROM rooms WHERE id = $1", [id]);
  return rows[0] ? toRoom(rows[0]) : null;
}

type ParticipantRow = {
  id: string;
  room_id: string;
  display_name: string;
  token: string;
  joined_at: string;
};
const toParticipant = (r: ParticipantRow): Participant => ({
  id: r.id,
  roomId: r.room_id,
  displayName: r.display_name,
  token: r.token,
  joinedAt: r.joined_at,
});

export async function addParticipant(
  roomId: string,
  displayName: string
): Promise<Participant> {
  const id = generateToken();
  const token = generateToken();
  const rows = await query<ParticipantRow>(
    `INSERT INTO participants (id, room_id, display_name, token)
     VALUES ($1,$2,$3,$4) RETURNING *`,
    [id, roomId, displayName, token]
  );
  return toParticipant(rows[0]);
}

export async function getParticipantByToken(
  roomId: string,
  token: string
): Promise<Participant | null> {
  const rows = await query<ParticipantRow>(
    "SELECT * FROM participants WHERE room_id = $1 AND token = $2",
    [roomId, token]
  );
  return rows[0] ? toParticipant(rows[0]) : null;
}

type MessageRow = {
  id: string;
  room_id: string;
  author_type: AuthorType;
  participant_id: string | null;
  author_name: string | null;
  body: string;
  contribution_tag: ContributionTag | null;
  created_at: string;
};
const toMessage = (r: MessageRow): Message => ({
  id: Number(r.id),
  roomId: r.room_id,
  authorType: r.author_type,
  participantId: r.participant_id,
  authorName: r.author_name,
  body: r.body,
  contributionTag: r.contribution_tag,
  createdAt: r.created_at,
});

const MESSAGE_SELECT = `
  SELECT m.id, m.room_id, m.author_type, m.participant_id,
         p.display_name AS author_name, m.body, m.contribution_tag, m.created_at
  FROM messages m
  LEFT JOIN participants p ON p.id = m.participant_id
`;

export async function addMessage(input: {
  roomId: string;
  authorType: AuthorType;
  participantId: string | null;
  body: string;
  contributionTag: ContributionTag | null;
}): Promise<Message> {
  const inserted = await query<{ id: string }>(
    `INSERT INTO messages (room_id, author_type, participant_id, body, contribution_tag)
     VALUES ($1,$2,$3,$4,$5) RETURNING id`,
    [input.roomId, input.authorType, input.participantId, input.body, input.contributionTag]
  );
  const rows = await query<MessageRow>(`${MESSAGE_SELECT} WHERE m.id = $1`, [inserted[0].id]);
  return toMessage(rows[0]);
}

export async function getMessages(roomId: string, sinceId: number): Promise<Message[]> {
  const rows = await query<MessageRow>(
    `${MESSAGE_SELECT} WHERE m.room_id = $1 AND m.id > $2 ORDER BY m.id ASC`,
    [roomId, sinceId]
  );
  return rows.map(toMessage);
}

export async function getAllMessages(roomId: string): Promise<Message[]> {
  return getMessages(roomId, 0);
}

export async function humanMessagesSinceLastClaude(roomId: string): Promise<number> {
  const rows = await query<{ count: string }>(
    `SELECT count(*)::text AS count FROM messages
     WHERE room_id = $1 AND author_type = 'human'
       AND id > COALESCE(
         (SELECT max(id) FROM messages WHERE room_id = $1 AND author_type = 'claude'), 0)`,
    [roomId]
  );
  return Number(rows[0].count);
}

export async function lastClaudeMessageAt(roomId: string): Promise<string | null> {
  const rows = await query<{ created_at: string }>(
    `SELECT created_at FROM messages
     WHERE room_id = $1 AND author_type = 'claude'
     ORDER BY id DESC LIMIT 1`,
    [roomId]
  );
  return rows[0]?.created_at ?? null;
}

type HarvestRow = { id: string; room_id: string; body: string; finalized_at: string | null };
const toHarvest = (r: HarvestRow): Harvest => ({
  id: Number(r.id),
  roomId: r.room_id,
  body: r.body,
  finalizedAt: r.finalized_at,
});

export async function saveHarvestDraft(roomId: string, body: string): Promise<Harvest> {
  const rows = await query<HarvestRow>(
    `INSERT INTO harvests (room_id, body) VALUES ($1,$2)
     ON CONFLICT (room_id) DO UPDATE SET body = EXCLUDED.body, finalized_at = NULL
     RETURNING *`,
    [roomId, body]
  );
  return toHarvest(rows[0]);
}

export async function finalizeHarvest(roomId: string, body: string): Promise<Harvest> {
  const rows = await query<HarvestRow>(
    `INSERT INTO harvests (room_id, body, finalized_at) VALUES ($1,$2, now())
     ON CONFLICT (room_id) DO UPDATE SET body = EXCLUDED.body, finalized_at = now()
     RETURNING *`,
    [roomId, body]
  );
  return toHarvest(rows[0]);
}

export async function getHarvest(roomId: string): Promise<Harvest | null> {
  const rows = await query<HarvestRow>("SELECT * FROM harvests WHERE room_id = $1", [roomId]);
  return rows[0] ? toHarvest(rows[0]) : null;
}

export type LobbyRoom = {
  id: string;
  nodeTitle: string;
  nodeDescription: string;
  participantCount: number;
  messageCount: number;
  lastActivityAt: string | null;
  createdAt: string;
};

export async function listRooms(): Promise<LobbyRoom[]> {
  const rows = await query<{
    id: string;
    node_title: string;
    node_description: string;
    created_at: string;
    participant_count: number;
    message_count: number;
    last_activity_at: string | null;
  }>(
    `SELECT r.id, r.node_title, r.node_description, r.created_at,
       COALESCE(p.cnt, 0)::int AS participant_count,
       COALESCE(m.cnt, 0)::int AS message_count,
       m.last_at AS last_activity_at
     FROM rooms r
     LEFT JOIN (SELECT room_id, count(*) AS cnt FROM participants GROUP BY room_id) p
       ON p.room_id = r.id
     LEFT JOIN (SELECT room_id, count(*) AS cnt, max(created_at) AS last_at FROM messages GROUP BY room_id) m
       ON m.room_id = r.id
     WHERE r.listed = true
     ORDER BY COALESCE(m.last_at, r.created_at) DESC`
  );
  return rows.map((r) => ({
    id: r.id,
    nodeTitle: r.node_title,
    nodeDescription: r.node_description,
    participantCount: r.participant_count,
    messageCount: r.message_count,
    lastActivityAt: r.last_activity_at,
    createdAt: r.created_at,
  }));
}

export async function setRoomListed(roomId: string, listed: boolean): Promise<void> {
  await query("UPDATE rooms SET listed = $2 WHERE id = $1", [roomId, listed]);
}

// Update any subset of the editable content fields. Column names come from a
// fixed map (never user input); values are parameterized.
export async function updateRoom(
  id: string,
  fields: { nodeTitle?: string; nodeDescription?: string; facilitationPrompt?: string }
): Promise<Room> {
  const columns: Record<keyof typeof fields, string> = {
    nodeTitle: "node_title",
    nodeDescription: "node_description",
    facilitationPrompt: "facilitation_prompt",
  };
  const sets: string[] = [];
  const values: unknown[] = [id];
  for (const key of Object.keys(columns) as (keyof typeof fields)[]) {
    const value = fields[key];
    if (value === undefined) continue;
    values.push(value);
    sets.push(`${columns[key]} = $${values.length}`);
  }
  if (sets.length === 0) {
    const room = await getRoom(id);
    if (!room) throw new Error(`room ${id} not found`);
    return room;
  }
  const rows = await query<RoomRow>(
    `UPDATE rooms SET ${sets.join(", ")} WHERE id = $1 RETURNING *`,
    values
  );
  return toRoom(rows[0]);
}
