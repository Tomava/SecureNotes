"use client";

import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { CONFIG } from "@/app/config";
import { encryptString, uint8ArrayToHex } from "@/app/helpers";
import bcrypt from "bcryptjs";
import { useRouter } from "next/navigation";

type FormData = {
  username: "";
  password: "";
};

const Signup: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    username: "",
    password: "",
  });
  const router = useRouter();

  useEffect(() => {
    if (localStorage.getItem("encryptionKey")) {
      router.push(CONFIG.NEXT_PUBLIC_FRONTEND_NOTES);
    }
  }, [router]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await createAccount();
  };

  const createAccount = async () => {
    const username = formData.username;
    const password = formData.password;
    const saltRounds = 10;

    // Create login hash to use for logging in
    const loginSalt = bcrypt.genSaltSync(saltRounds);
    const loginHash = bcrypt.hashSync(password, loginSalt);

    // Create encryption hash to encrypt encryption key
    const encryptionSalt = bcrypt.genSaltSync(saltRounds);
    const encryptionHash = bcrypt.hashSync(password, encryptionSalt);

    // Create encryption key and encrypt it
    const buf = new Uint8Array(32);
    crypto.getRandomValues(buf);
    const encryptionKey = uint8ArrayToHex(buf);
    const encryptedKey = encryptString(encryptionKey, encryptionHash);

    const sendingData = {
      username: username,
      front_login_hash: loginHash,
      front_login_salt: loginSalt,
      encryption_salt: encryptionSalt,
      encrypted_encryption_key: encryptedKey,
    };

    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_SIGNUP}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(sendingData),
      }
    );
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
          <input type="submit" value="Sign up" />
        </form>
      </div>
    </main>
  );
};

export default Signup;
