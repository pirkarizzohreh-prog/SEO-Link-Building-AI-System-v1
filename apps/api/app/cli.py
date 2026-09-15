"""Tiny management CLI — currently just the admin-bootstrap command.

There is no public registration endpoint (this is an internal tool), and
`POST /users` is admin-only, so the very first user has to be created
out-of-band:

    python -m app.cli create-admin --name "Ada" --email ada@example.com --password "..."

Usage mirrors Django's `createsuperuser` / a Rails `db:seed` task.
"""

from __future__ import annotations

import argparse
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def create_admin(name: str, email: str, password: str) -> None:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first() is not None:
            print(f"A user with email {email!r} already exists.", file=sys.stderr)
            raise SystemExit(1)

        user = User(name=name, email=email, password_hash=hash_password(password), role=UserRole.ADMIN)
        db.add(user)
        db.commit()
        print(f"Created admin user {email!r} (id={user.id}).")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_admin_parser = subparsers.add_parser("create-admin", help="Create the first admin user")
    create_admin_parser.add_argument("--name", required=True)
    create_admin_parser.add_argument("--email", required=True)
    create_admin_parser.add_argument("--password", required=True)

    args = parser.parse_args()
    if args.command == "create-admin":
        create_admin(args.name, args.email, args.password)


if __name__ == "__main__":
    main()
