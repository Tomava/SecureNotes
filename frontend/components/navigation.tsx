import Link from "next/link";
import styles from "./navigation.module.css";
import { CONFIG } from "@/app/config";

const Navigation: React.FC = () => {
  return (
    <nav className={styles.navigation}>
      <Link href={CONFIG.NEXT_PUBLIC_FRONTEND_NOTES}>
        <button className={styles.button}>Notes</button>
      </Link>
      <Link href={CONFIG.NEXT_PUBLIC_FRONTEND_LOGOUT}>
        <button className={styles.button}>Log out page</button>
      </Link>
    </nav>
  );
};

export default Navigation;
