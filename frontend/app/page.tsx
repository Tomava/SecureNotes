import Image from "next/image";
import styles from "./page.module.scss";
import { redirect } from 'next/navigation'
import { CONFIG } from "@/app/config";

export default function Home() {
    redirect(CONFIG.NEXT_PUBLIC_FRONTEND_LOGIN);
    return (
    <main className={styles.main}>
      <div>
      Hello World!
      </div>
    </main>
  );
}
