import { notFound } from "next/navigation";
import { getRoom } from "@/lib/rooms";
import { RoomClient } from "./RoomClient";

export default async function RoomPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const room = await getRoom(id);
  if (!room) notFound();
  return (
    <RoomClient
      roomId={room.id}
      nodeTitle={room.nodeTitle}
      nodeDescription={room.nodeDescription}
    />
  );
}
