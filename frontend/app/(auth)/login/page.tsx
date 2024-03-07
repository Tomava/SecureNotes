"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { CONFIG } from "@/app/config";
import { decryptString, encryptString, uint8ArrayToHex } from "@/app/helpers";
import bcrypt from "bcryptjs";

type FormData = {
  username: "";
  password: "";
};

const Login: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    username: "",
    password: "",
  });

  const [encryptionKey, setEncryptionKey] = useState("");

  useEffect(() => {
    localStorage.setItem('encryptionKey', JSON.stringify(encryptionKey));
  }, [encryptionKey]);


  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await login();
  };

  const login = async () => {
    const username = formData.username;
    const password = formData.password;

    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_GET_HASH}?username=${username}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    const hashData = (await response.json()).data;

    // Create login hash to use for logging in
    const loginSalt = hashData.front_login_salt;
    const loginHash = bcrypt.hashSync(password, loginSalt);

    const response2 = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_LOGIN}?username=${username}&front_login_hash=${loginHash}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include"
        }
    );

    const loginData = (await response2.json()).data;

    const encryptedEncryptionKey = loginData.encrypted_encryption_key;
    const encryptionSalt = loginData.encryption_salt;

    const encryptionHash = bcrypt.hashSync(password, encryptionSalt);
    setEncryptionKey(decryptString(encryptedEncryptionKey, encryptionHash));
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  // TODO: Add CSRF tag
  return (
    <main>
      <div>
        <form method="post" onSubmit={handleSubmit}>
          <label htmlFor="username">Username:</label>
          <br />
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
          />
          <br />
          <label htmlFor="password">Password:</label>
          <br />
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
          />
          <br />
          <input type="submit" value="Login" />
        </form>
      </div>
    </main>
  );
};

export default Login;
