"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { CONFIG } from "@/app/config";
import {
  decryptString,
  encryptString,
  fetchCsrf,
  setBanner,
} from "@/app/helpers";
import Note from "@/components/note";
import styles from "./page.module.scss";
import { useRouter } from "next/navigation";
import Navigation from "@/components/navigation";
import { ErrorBanner } from "@/components/banner";

export type NoteData = {
  title: string;
  body: string;
};

export type ParsedNoteData = {
  createdAt: number;
  modifiedAt: number;
  noteData: NoteData;
  noteId: string;
};

const Notes: React.FC = () => {
  const [notes, setNotes] = useState<ParsedNoteData[]>([]);
  const [encryptionKey, setEncryptionKey] = useState("");
  const [formData, setFormData] = useState<NoteData>({
    title: "",
    body: "",
  });
  const [errorBannerText, setErrorBannerText] = useState("");
  const [csrfToken, setCsrfToken] = useState("");
  const router = useRouter();

  useEffect(() => {
    const encKey = localStorage.getItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY);
    if (encKey) {
      setEncryptionKey(encKey);
    }
  }, []);

  useEffect(() => {
    if (!localStorage.getItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY)) {
      router.push(CONFIG.NEXT_PUBLIC_FRONTEND_LOGIN);
    }
  }, [router]);

  useEffect(() => {
    const fetchData = async () => {
      if (!encryptionKey) {
        return;
      }
      const formatNoteData = (
        encryptedTitle: string,
        encryptedBody: string
      ): NoteData => {
        if (encryptionKey) {
          const decryptedData: NoteData = {
            title: decryptString(encryptedTitle, encryptionKey),
            body: decryptString(encryptedBody, encryptionKey),
          };
          return decryptedData;
        }
        return { title: "", body: "" };
      };
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
            noteData: formatNoteData(note.note_title, note.note_body),
            noteId: note.note_id,
          }))
        );
      }
    };
    fetchData().catch(console.error);
  }, [encryptionKey]);

  useEffect(() => {
    if (!csrfToken) {
      fetchCsrf()
        .then((csrfTokenResponse) => setCsrfToken(csrfTokenResponse))
        .catch(console.error);
    }
  }, [csrfToken]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await createNote();
  };

  const createNote = async () => {
    const title = formData.title;
    const body = formData.body;

    if (!encryptionKey) {
      console.error("Can't encrypt without encryption key!");
      return;
    }
    const encryptedTitle = encryptString(title, encryptionKey);
    const encryptedBody = encryptString(body, encryptionKey);

    const sendingData = {
      note_title: encryptedTitle,
      note_body: encryptedBody,
    };

    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_NOTES}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(sendingData),
        credentials: "include",
      }
    );

    const responseJson = await response.json();

    if (response.status != 201) {
      let message = "Not saved:\n";
      if (responseJson.error == "TooLarge") {
        message += "Note was too large";
      } else if (responseJson.error == "TooMany") {
        message += "Too many notes already";
      } else {
        message += "Error when saving";
      }
      setBanner(message, setErrorBannerText, 5000);
    }

    const responseData = responseJson.data;
    const addedNote = {
      createdAt: responseData.created_at,
      modifiedAt: responseData.modified_at,
      noteData: { title: title, body: body },
      noteId: responseData.note_id,
    };
    setNotes([...notes, addedNote]);
  };

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  return (
    <>
      <Navigation loggedIn={true} />
      <main>
        {errorBannerText && <ErrorBanner text={errorBannerText} />}
        <div className={styles.main}>
          <div id="new-note">
            <h2>Create new</h2>
            <form method="post" onSubmit={handleSubmit}>
              <label htmlFor="title">Title:</label>
              <br />
              <input
                type="text"
                id="title"
                name="title"
                value={formData.title}
                onChange={handleChange}
              />
              <br />
              <label htmlFor="body">Body:</label>
              <br />
              <textarea
                id="body"
                name="body"
                value={formData.body}
                onChange={handleChange}
              />
              <br />
              <input type="submit" value="Create" />
            </form>
          </div>
          <div id="notes">
            <h2>Notes</h2>
            <ul id="notesList" className={styles.notesList}>
              {notes.map((note) => (
                <Note key={note.noteId} noteData={note} />
              ))}
            </ul>
          </div>
        </div>
      </main>
    </>
  );
};

export default Notes;
