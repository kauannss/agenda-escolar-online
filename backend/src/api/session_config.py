import os

from dotenv import load_dotenv

load_dotenv()


SESSION_COOKIE_NAME = "agenda_session"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "43200"))
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "lax").lower()

if SESSION_TTL_SECONDS <= 0:
    raise ValueError("SESSION_TTL_SECONDS must be greater than zero.")

if SESSION_COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise ValueError("SESSION_COOKIE_SAMESITE must be lax, strict, or none.")

if SESSION_COOKIE_SAMESITE == "none" and not SESSION_COOKIE_SECURE:
    raise ValueError("SESSION_COOKIE_SECURE must be true when SameSite is none.")
