import Link from "next/link";
import styles from "./navigation.module.scss";
import { CONFIG } from "@/app/config";

type NavigationProps = {
  loggedIn: boolean;
};

const Navigation: React.FC<NavigationProps> = ({loggedIn}) => {
  return (
    <nav className={styles.navigation}>
      {loggedIn && <Link href={CONFIG.NEXT_PUBLIC_FRONTEND_NOTES}>
        <button className={styles.button}>Notes</button>
      </Link>}
      {loggedIn && <Link href={CONFIG.NEXT_PUBLIC_FRONTEND_LOGOUT}>
        <button className={styles.button}>Log out</button>
      </Link>}
      {loggedIn && <Link href={CONFIG.NEXT_PUBLIC_FRONTEND_SETTINGS}>
        <button className={styles.button}>Settings</button>
      </Link>}
      {!loggedIn && <Link href={CONFIG.NEXT_PUBLIC_FRONTEND_SIGNUP}>
        <button className={styles.button}>Sign up</button>
      </Link>}
      {!loggedIn && <Link href={CONFIG.NEXT_PUBLIC_FRONTEND_LOGIN}>
        <button className={styles.button}>Log in</button>
      </Link>}
    </nav>
  );
};

export default Navigation;
