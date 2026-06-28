import { notFound } from "next/navigation";
import { getRoom } from "@/lib/rooms";
import { ManageClient } from "./ManageClient";

export default async function ManagePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const room = await getRoom(id);
  if (!room) notFound();
  return <ManageClient roomId={room.id} nodeTitle={room.nodeTitle} listed={room.listed} />;
}
