import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g
from config import Config


def generate_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRES_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])


def _extract_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def login_required(fn):
    """Validates the JWT and attaches g.user_id / g.user_role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        g.user_id = payload["sub"]
        g.user_role = payload["role"]
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """Standalone decorator — validates the token AND restricts to ADMIN role.
    Use this instead of stacking it with login_required."""

    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if g.user_role != "ADMIN":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)

    return wrapper
