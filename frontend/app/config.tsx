import dotenv from 'dotenv';

dotenv.config();

export const CONFIG = {
  NEXT_PUBLIC_BACKEND_ROOT: process.env.NEXT_PUBLIC_BACKEND_ROOT || "localhost:5000",
  NEXT_PUBLIC_BACKEND_SIGNUP: "/signup",
  NEXT_PUBLIC_BACKEND_GET_HASH: "/hash",
  NEXT_PUBLIC_BACKEND_LOGIN: "/login",
  NEXT_PUBLIC_BACKEND_NOTES: "/notes"
}
