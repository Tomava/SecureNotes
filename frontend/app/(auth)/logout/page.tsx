"use client";

import { MouseEvent, useEffect, useState } from "react";
import { CONFIG } from "@/app/config";
import { useRouter } from "next/navigation";
import { ErrorBanner } from "@/components/banner";
import { fetchCsrf, setBanner } from "@/app/helpers";
import Navigation from "@/components/navigation";

const Logout: React.FC = () => {
  const [errorBannerText, setErrorBannerText] = useState("");
  const [isLoggedOut, setIsLoggedOut] = useState(false);
  const [loggedSessionCount, setLoggedSessionCount] = useState(0);
  const [csrfToken, setCsrfToken] = useState("");
  const router = useRouter();

  const handleLogout = async (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    await logout(false);
  };

  const handleLogoutAll = async (e: MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    await logout(true);
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
      fetchCsrf()
        .then((csrfTokenResponse) => setCsrfToken(csrfTokenResponse))
        .catch(console.error);
    }
  }, [csrfToken]);

  useEffect(() => {
    async function fetchData() {
      if (!loggedSessionCount) {
        const response = await fetch(
          `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_SESSION}`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
            },
            credentials: "include",
          }
        );
        const responseData = (await response.json()).data;
        if (responseData && responseData.sessions) {
          setLoggedSessionCount(responseData.sessions);
        }
      }
    }
    fetchData().then();
  }, [loggedSessionCount]);

  const logout = async (all: boolean) => {
    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_LOGOUT}${all ? "?all=true" : ""}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
      }
    );

    setIsLoggedOut(true);
  };

  return (
    <>
      <Navigation loggedIn={true} />
      <main>
        {errorBannerText && <ErrorBanner text={errorBannerText} />}
        <div>
          <button onClick={handleLogout}>Logout from this session</button>
          {!!loggedSessionCount && (
            <button onClick={handleLogoutAll}>Logout from all {loggedSessionCount} sessions</button>
          )}
        </div>
      </main>
    </>
  );
};

export default Logout;
