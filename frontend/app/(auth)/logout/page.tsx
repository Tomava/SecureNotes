"use client";

import { MouseEvent, useEffect, useState } from "react";
import { CONFIG } from "@/app/config";
import { useRouter } from "next/navigation";
import Banner from "@/components/banner";
import { fetchCsrf } from "@/app/helpers";

const Logout: React.FC = () => {
  const [bannerText, setBannerText] = useState("");
  const [isLoggedOut, setIsLoggedOut] = useState(false);
  const [csrfToken, setCsrfToken] = useState("");
  const router = useRouter();

  const setBanner = (text: string) => {
    setBannerText(text);
    setTimeout(() => {
      setBannerText("");
    }, 5000);
  };

  const handleLogout = async (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    await logout();
  };

  useEffect(() => {
    if (!localStorage.getItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY)) {
      router.push(CONFIG.NEXT_PUBLIC_FRONTEND_LOGIN);
    }
  }, [router]);

  useEffect(() => {
    if (isLoggedOut) {
      localStorage.removeItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY);
      router.push(CONFIG.NEXT_PUBLIC_FRONTEND_LOGIN);
    }
  }, [isLoggedOut, router]);

  useEffect(() => {
    if (!csrfToken) {
      fetchCsrf().then((csrfTokenResponse) => setCsrfToken(csrfTokenResponse)).catch(console.error);
    }
  }, [csrfToken]);

  const logout = async () => {
    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_LOGOUT}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
      }
    );

    if (response.status != 200) {
      setBanner("Error while logging out!");
      return;
    }

    setIsLoggedOut(true);
  };

  return (
    <main>
      {bannerText && <Banner text={bannerText} />}
      <div>
        <div>
          List of logged in sessions:
          <ul></ul>
        </div>
        <div>
          <button onClick={handleLogout}>Logout from this session</button>
          <button>Logout from everywhere</button>
        </div>
      </div>
    </main>
  );
};

export default Logout;
