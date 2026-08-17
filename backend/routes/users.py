from flask import Blueprint, request, jsonify, g
from extensions import get_supabase
from utils.auth_decorators import admin_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.get("")
@admin_required
def list_users():
    db = get_supabase()
    search = request.args.get("search", "").strip()
    query = db.table("users").select("id,name,email,role,status,created_at").eq("role", "STUDENT")
    if search:
        query = query.ilike("name", f"%{search}%")
    result = query.execute()
    return jsonify(result.data)


@users_bp.get("/<user_id>")
@admin_required
def get_user(user_id):
    db = get_supabase()
    result = db.table("users").select("id,name,email,role,status,created_at").eq("id", user_id).execute()
    if not result.data:
        return jsonify({"error": "User not found"}), 404
    return jsonify(result.data[0])


@users_bp.put("/<user_id>")
@admin_required
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    allowed = {k: v for k, v in data.items() if k in ("name", "email")}
    if not allowed:
        return jsonify({"error": "Nothing to update"}), 400
    db = get_supabase()
    result = db.table("users").update(allowed).eq("id", user_id).execute()
    if not result.data:
        return jsonify({"error": "User not found"}), 404
    return jsonify(result.data[0])


@users_bp.delete("/<user_id>")
@admin_required
def delete_user(user_id):
    db = get_supabase()
    db.table("users").delete().eq("id", user_id).execute()
    return jsonify({"message": "User deleted"})


@users_bp.patch("/<user_id>/status")
@admin_required
def update_user_status(user_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("ACTIVE", "INACTIVE"):
        return jsonify({"error": "status must be ACTIVE or INACTIVE"}), 400
    db = get_supabase()
    result = db.table("users").update({"status": status}).eq("id", user_id).execute()
    if not result.data:
        return jsonify({"error": "User not found"}), 404
    return jsonify(result.data[0])
