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
  const [csrfToken, setCsrfToken] = useState("");
  const router = useRouter();

  useEffect(() => {
    if (!localStorage.getItem(CONFIG.NEXT_PUBLIC_ENCRYPTION_KEY)) {
      router.push(CONFIG.NEXT_PUBLIC_FRONTEND_LOGIN);
    }
  }, [router]);
  useEffect(() => {
    if (!csrfToken) {
      fetchCsrf()
        .then((csrfTokenResponse) => setCsrfToken(csrfTokenResponse))
        .catch(console.error);
    }
  }, [csrfToken]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await addOtp();
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
  };

  return (
    <>
      <Navigation loggedIn={true} />
      <main>
        {errorBannerText && <ErrorBanner text={errorBannerText} />}
        {bannerText && <Banner text={bannerText} />}
        <div>
          <form method="post" onSubmit={handleSubmit}>
            <input type="submit" value="Add OTP" />
          </form>
          {otpUri && (
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
