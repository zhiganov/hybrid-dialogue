import Anthropic from "@anthropic-ai/sdk";
import type { Message, Room } from "./rooms";

const STANCE = `You are a quiet facilitator in a small, asynchronous group conversation.
People drop in over hours or days, so they often will not be present at the same time.
Your role is to amplify human-to-human dialogue, not to replace it:
- Encourage people to respond to each other, not to you.
- Synthesize and connect rather than opine or lecture.
- Surface connections between what different people have said, especially across visits.
- Stay brief. Speak only when it adds something a participant could not easily add themselves.
- Never use em dashes. Use commas, colons, periods, or parentheses instead.`;

function client(): Anthropic {
  if (!process.env.ANTHROPIC_API_KEY) throw new Error("ANTHROPIC_API_KEY is not set");
  return new Anthropic();
}

function frame(room: Room): string {
  return `The conversation node is titled: "${room.nodeTitle}".
Description: ${room.nodeDescription}
Facilitation guidance for you: ${room.facilitationPrompt}`;
}

function transcript(messages: Message[]): string {
  return messages
    .map((m) => {
      const who = m.authorType === "claude" ? "Facilitator" : m.authorName ?? "Someone";
      const tag = m.contributionTag ? ` [${m.contributionTag}]` : "";
      return `${who}${tag}: ${m.body}`;
    })
    .join("\n");
}

// Short, snappy reply when a participant writes @claude.
export async function replyToMention(room: Room, recent: Message[]): Promise<string> {
  const res = await client().messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1024,
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Recent messages:
${transcript(recent)}

A participant addressed you with @claude. Respond briefly and helpfully, then hand the thread back to the group. Do not summarize the whole conversation; answer what was asked.`,
      },
    ],
  });
  return textOf(res);
}

// Periodic weave: one synthesis / connection / opening question.
export async function weave(room: Room, recent: Message[]): Promise<string> {
  const stream = client().messages.stream({
    model: "claude-sonnet-4-6",
    max_tokens: 2048,
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Recent contributions:
${transcript(recent)}

Post ONE short weave. Pick the single most useful move right now: name a connection between two people's contributions, offer a brief synthesis of an emerging thread, or ask one opening question. Two or three sentences. Address the group, not any one person, and invite them to keep talking to each other.`,
      },
    ],
  });
  return textOf(await stream.finalMessage());
}

// Opening frame posted when the room is created.
export async function openingFrame(room: Room): Promise<string> {
  const stream = client().messages.stream({
    model: "claude-haiku-4-5-20251001",
    max_tokens: 2048,
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Write a short opening frame (three or four sentences) that welcomes people into this conversation and invites a first contribution. Warm, plain, and specific to the node. Do not list rules.`,
      },
    ],
  });
  return textOf(await stream.finalMessage());
}

// Harvest: distill the whole conversation into an editable draft.
export async function harvestDraft(room: Room, all: Message[]): Promise<string> {
  const stream = client().messages.stream({
    model: "claude-sonnet-4-6",
    max_tokens: 4096,
    system: STANCE,
    messages: [
      {
        role: "user",
        content: `${frame(room)}

Full conversation:
${transcript(all)}

Distill this into a harvest a human will edit and carry forward. Include:
1. A short title (one line).
2. The two or three threads that mattered most, each in a sentence or two, grounded in what people actually said.
3. Any open question worth carrying into the next conversation.
Keep it tight and faithful. This is a draft for a human to refine, not a transcript.`,
      },
    ],
  });
  return textOf(await stream.finalMessage());
}

function textOf(message: Anthropic.Message): string {
  return message.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("")
    // Enforce the STANCE no-em-dash rule in code; models (Haiku especially) slip.
    .replace(/\s*[—–]\s*/g, ", ")
    .replace(/,\s*,/g, ",")
    .trim();
}
