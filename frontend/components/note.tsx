import { ParsedNoteData } from "@/app/notes/page";
import styles from "./note.module.scss";

const Note: React.FC<{ noteData: ParsedNoteData }> = ({ noteData }) => {
  return (
    <li key={noteData.noteId} className={styles.note}>
      <h3 className={styles.title}>{noteData.noteData.title}</h3>
      <p className={styles.body}>{noteData.noteData.body}</p>
    </li>
  );
};

export default Note;
