export async function handler(req) {
  const id = req.body.note_id;
  return db.from("notes").select("*").eq("id", id);
}
