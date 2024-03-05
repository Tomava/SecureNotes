import CryptoJS from "crypto-js";


export const uint8ArrayToHex = (uint8Array: Uint8Array): string => {
  return Array.from(uint8Array, (byte) =>
    byte.toString(16).padStart(2, "0")
  ).join("");
};

export const encryptString = (plainText: string, key: string): string => {
  return CryptoJS.AES.encrypt(plainText, key).toString();
}

export const decryptString = (cipherText: string, key: string): string => {
  return CryptoJS.AES.decrypt(cipherText, key).toString(CryptoJS.enc.Utf8);
}
