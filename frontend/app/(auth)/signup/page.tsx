"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import { CONFIG } from "../../config";

type FormData = {
  username: "";
  password: "";
};

const Signup: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    username: "",
    password: "",
  });

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await createAccount();
  };

  const createAccount = async () => {
    const username = formData.username;
    const password = formData.password;
    const sendingData = {username: username, password: password};
    const response = await fetch(
      `${CONFIG.NEXT_PUBLIC_BACKEND_ROOT}${CONFIG.NEXT_PUBLIC_BACKEND_SIGNUP}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(sendingData)
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
