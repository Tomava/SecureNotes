import unittest
from config import *
import main

class TestBackend(unittest.TestCase):
    def test_hashing(self):
        hashed_pw = main.hash_password("password")
        self.assertEqual(len(hashed_pw), LOGIN_HASH_LEN)
        self.assertTrue(hashed_pw.startswith("$argon2id$v=19$m=65536,t=3,p=4$"))

    def test_verify(self):
        password = "password"
        hashed_pw = main.hash_password(password)
        self.assertTrue(main.verify_password(hashed_pw, password))


if __name__ == "__main__":
    unittest.main()
