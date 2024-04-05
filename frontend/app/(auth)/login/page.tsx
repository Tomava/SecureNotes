"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { CONFIG } from "@/app/config";
import { decryptString, setBanner } from "@/app/helpers";
import bcrypt from "bcryptjs";
import { Banner, ErrorBanner } from "@/components/banner";
import { useRouter } from "next/navigation";
import Navigation from "@/components/navigation";
import styles from "./page.module.scss";

type FormData = {
  username: string;
  password: string;
  otpCode: string;
};

const Login: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    username: "",
    password: "",
    otpCode: "",
  });

  const [encryptionKey, setEncryptionKey] = useState("");
  const [bannerText, setBannerText] = useState("");
  const [errorBannerText, setErrorBannerText] = useState("");
  const [showOTP, setShowOTP] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (encryptionKey) {
      localStorage.setItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY, encryptionKey);
    }
  }, [encryptionKey]);

  useEffect(() => {
    if (localStorage.getItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY)) {
      router.push(CONFIG.NEXT_PUBLIC_FRONTEND_NOTES);
    }
  }, [router]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await login();
  };

  const login = async () => {
    const username = formData.username;
    const password = formData.password;
    const otpCode = formData.otpCode;

    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_GET_HASH}?username=${username}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (response.status != 200) {
      setBanner("Incorrect credentials!", setErrorBannerText, 5000);
      return;
    }

    const hashData = (await response.json()).data;

    // Create login hash to use for logging in
    const loginSalt = hashData.front_login_salt;
    const loginHash = bcrypt.hashSync(password, loginSalt);

    const response2 = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_LOGIN}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          username: username,
          front_login_hash: loginHash,
          otp_code: otpCode,
        }),
      }
    );

    const response2Data = await response2.json();

    if (response2.status != 200) {
      if (response2Data.error == "InvalidOTP") {
        if (!showOTP) {
          setShowOTP(true);
        } else {
          setBanner("Incorrect OTP code", setErrorBannerText, 5000);
        }
      } else {
        setBanner("Incorrect credentials!", setErrorBannerText, 5000);
      }
      return;
    }

    const loginData = response2Data.data;

    const encryptedEncryptionKey = loginData.encrypted_encryption_key;
    const encryptionSalt = loginData.encryption_salt;

    const encryptionHash = bcrypt.hashSync(password, encryptionSalt);
    setEncryptionKey(decryptString(encryptedEncryptionKey, encryptionHash));
    if (showOTP) {
      localStorage.setItem(CONFIG.NEXT_PUBLIC_OTP_CODE, "true");
    }

    setBanner("", setErrorBannerText, 5000);
    setBanner("Logged in!", setBannerText, 5000);
    router.push(CONFIG.NEXT_PUBLIC_FRONTEND_NOTES);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  return (
    <>
      <Navigation loggedIn={false} />
      <main className={styles.main}>
        {errorBannerText && <ErrorBanner text={errorBannerText} />}
        {bannerText && <Banner text={bannerText} />}
        <div>
          <form method="post" onSubmit={handleSubmit}>
            {showOTP ? (
              <>
                <label htmlFor="otpCode" className={styles.label}>OTP code:</label>
                <br />
                <input
                  type="text"
                  id="otpCode"
                  name="otpCode"
                  value={formData.otpCode}
                  onChange={handleChange}
                  maxLength={6}
                />
                <br />
              </>
            ) : (
              <>
                <label htmlFor="username" className={styles.label}>Username:</label>
                <br />
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  maxLength={CONFIG.NEXT_PUBLIC_USERNAME_LENGTH}
                />
                <br />
                <label htmlFor="password" className={styles.label}>Password:</label>
                <br />
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                />
                <br />
              </>
            )}
            <input type="submit" value="Login" />
          </form>
        </div>
      </main>
    </>
  );
};

export default Login;
