"use client";

import { FormEvent, useEffect, useState } from "react";
import { CONFIG } from "@/app/config";
import { fetchCsrf, setBanner } from "@/app/helpers";
import QRCode from "react-qr-code";
import { useRouter } from "next/navigation";
import { Banner, ErrorBanner } from "@/components/banner";
import Navigation from "@/components/navigation";

const Otp: React.FC = () => {
  const [bannerText, setBannerText] = useState("");
  const [errorBannerText, setErrorBannerText] = useState("");
  const [otpUri, setOtpUri] = useState("");
  const [otpSecret, setOtpSecret] = useState("");
  const [loading, setLoading] = useState(true);
  const [otpExists, setOtpExists] = useState(false);
  const [csrfToken, setCsrfToken] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!localStorage.getItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY)) {
      router.push(CONFIG.NEXT_PUBLIC_FRONTEND_LOGIN);
    }
  }, [router]);

  useEffect(() => {
    if (localStorage.getItem(CONFIG.NEXT_PUBLIC_OTP_CODE)) {
      setOtpExists(true);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!csrfToken) {
      fetchCsrf()
        .then((csrfTokenResponse) => setCsrfToken(csrfTokenResponse))
        .catch(console.error);
    }
  }, [csrfToken]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (otpExists) {
      await removeOtp();
    } else {
      await addOtp();
    }
  };

  const removeOtp = async () => {
    // TODO: Ask for OTP

    await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_OTP}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
      }
    );

    localStorage.removeItem(CONFIG.NEXT_PUBLIC_OTP_CODE);
    setOtpExists(false);
  };

  const addOtp = async () => {
    // TODO: Ask for password

    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_OTP}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        credentials: "include",
      }
    );

    if (response.status != 201) {
      setBanner("Invalid credentials!", setErrorBannerText, 5000);
      return;
    }

    const otpData = (await response.json()).data;

    setOtpSecret(otpData.otp_secret);
    setOtpUri(otpData.otp_uri);
    localStorage.setItem(CONFIG.NEXT_PUBLIC_OTP_CODE, "true");
    setOtpExists(true);
  };

  return (
    <>
      <Navigation loggedIn={true} />
      <main>
        {errorBannerText && <ErrorBanner text={errorBannerText} />}
        {bannerText && <Banner text={bannerText} />}
        <div>
          {!loading && <form method="post" onSubmit={handleSubmit}>
            <input type="submit" value={otpExists ? "Remove OTP" : "Add OTP"} />
          </form>}
          {otpUri && otpExists && (
            <div>
              <QRCode value={otpUri} />
              <p>{otpSecret}</p>
            </div>
          )}
        </div>
      </main>
    </>
  );
};

export default Otp;
