from flask import Blueprint, request, jsonify
from extensions import get_supabase
from utils.auth_decorators import admin_required

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@categories_bp.get("")
def list_categories():
    db = get_supabase()
    result = db.table("categories").select("*").order("name").execute()
    return jsonify(result.data)


@categories_bp.post("")
@admin_required
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    db = get_supabase()
    result = db.table("categories").insert({"name": name, "description": data.get("description")}).execute()
    return jsonify(result.data[0]), 201


@categories_bp.put("/<category_id>")
@admin_required
def update_category(category_id):
    data = request.get_json(silent=True) or {}
    allowed = {k: v for k, v in data.items() if k in ("name", "description")}
    if not allowed:
        return jsonify({"error": "Nothing to update"}), 400
    db = get_supabase()
    result = db.table("categories").update(allowed).eq("id", category_id).execute()
    if not result.data:
        return jsonify({"error": "Category not found"}), 404
    return jsonify(result.data[0])


@categories_bp.delete("/<category_id>")
@admin_required
def delete_category(category_id):
    db = get_supabase()
    db.table("categories").delete().eq("id", category_id).execute()
    return jsonify({"message": "Category deleted"})
