import CryptoJS from "crypto-js";
import { CONFIG } from "@/app/config";
import { Dispatch, SetStateAction } from "react";

export const uint8ArrayToHex = (uint8Array: Uint8Array): string => {
  return Array.from(uint8Array, (byte) =>
    byte.toString(16).padStart(2, "0")
  ).join("");
};

export const encryptString = (plainText: string, key: string): string => {
  return CryptoJS.AES.encrypt(plainText, key).toString();
};

export const decryptString = (cipherText: string, key: string): string => {
  return CryptoJS.AES.decrypt(cipherText, key).toString(CryptoJS.enc.Utf8);
};

export const fetchCsrf = async (): Promise<string> => {
  const response = await fetch(
    `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_CSRF}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    }
  );
  if (response.status != 200) {
    return "";
  }
  const responseData = (await response.json()).data;
  const csrfTokenResponse: string | undefined = responseData.csrf_token;
  return csrfTokenResponse || "";
};

export const setBanner = (text: string, setBannerText: Dispatch<SetStateAction<string>>, timeout: number) => {
  setBannerText(text);
  setTimeout(() => {
    setBannerText("");
  }, timeout);
};