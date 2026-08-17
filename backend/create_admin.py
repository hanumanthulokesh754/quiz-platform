"""One-off CLI to create an Admin account.

Registration (/api/auth/register) only ever creates STUDENT accounts, so the
first Admin has to be created this way — matches the spec's note that admin
accounts are created manually by the system owner.

Usage:
    python create_admin.py
"""
import getpass
import bcrypt
from extensions import get_supabase


def main():
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (min 8 chars): ")

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    db = get_supabase()
    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        print("A user with that email already exists.")
        return

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.table("users").insert({
        "name": name, "email": email, "password": hashed, "role": "ADMIN",
    }).execute()
    print(f"Admin account created for {email}.")


if __name__ == "__main__":
    main()
