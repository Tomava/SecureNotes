"use client";

import {
  ChangeEvent,
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";
import { CONFIG } from "@/app/config";
import { decryptString, encryptString, uint8ArrayToHex } from "@/app/helpers";
import bcrypt from "bcryptjs";

type NotesData = {
  createdAt: number;
  modifiedAt: number;
  noteData: string;
  noteId: string;
};

const Notes: React.FC = () => {
  const [notes, setNotes] = useState<NotesData[]>([]);
  const [encryptionKey, setEncryptionKey] = useState("");

  useEffect(() => {
    const encKey = localStorage.getItem("encryptionKey");
    if (encKey) {
      setEncryptionKey(encKey);
    }
  }, []);

  const fetchData = useCallback(async () => {
    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_NOTES}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      }
    );
    const responseData = (await response.json()).data;
    if (responseData && responseData.notes) {
      setNotes(
        responseData.notes.map((note: any) => ({
          createdAt: note.created_at,
          modifiedAt: note.modified_at,
          noteData: note.note_data,
          noteId: note.note_id,
        }))
      );
    }
  }, []);

  useEffect(() => {
    fetchData().catch(console.error);
  }, [fetchData]);

  return (
    <main>
      <div id="notes">
        <h2>Notes</h2>
        {notes.map((note) => (
          <p key={note.noteId}>{note.noteData}</p>
        ))}
      </div>
    </main>
  );
};

export default Notes;
