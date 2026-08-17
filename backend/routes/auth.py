import bcrypt
from flask import Blueprint, request, jsonify
from extensions import get_supabase
from utils.auth_decorators import generate_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    db = get_supabase()
    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        return jsonify({"error": "An account with this email already exists"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    result = (
        db.table("users")
        .insert({"name": name, "email": email, "password": hashed, "role": "STUDENT"})
        .execute()
    )
    user = result.data[0]
    token = generate_token(user["id"], user["role"])

    return jsonify({
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]},
    }), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    db = get_supabase()
    result = db.table("users").select("*").eq("email", email).execute()
    if not result.data:
        return jsonify({"error": "Invalid email or password"}), 401

    user = result.data[0]
    if user["status"] != "ACTIVE":
        return jsonify({"error": "This account has been deactivated"}), 403
    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(user["id"], user["role"])
    return jsonify({
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]},
    })


@auth_bp.post("/logout")
def logout():
    # JWTs are stateless — logout is handled client-side by discarding the token.
    # A token-blocklist table could be added here later if immediate revocation is needed.
    return jsonify({"message": "Logged out"})


@auth_bp.post("/forgot-password")
def forgot_password():
    # Stub: in production, generate a signed reset token, email it via
    # Supabase/SMTP, and store its hash + expiry against the user row.
    return jsonify({"message": "If that email exists, a reset link has been sent"}), 200


@auth_bp.post("/reset-password")
def reset_password():
    # Stub: verify the reset token from forgot-password, then update the
    # user's password hash. Left as a TODO for when email sending is wired up.
    return jsonify({"error": "Not implemented yet"}), 501
