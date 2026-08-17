from flask import Blueprint, request, jsonify, g
from extensions import get_supabase
from utils.auth_decorators import admin_required, login_required

quizzes_bp = Blueprint("quizzes", __name__, url_prefix="/api/quizzes")


@quizzes_bp.get("")
@login_required
def list_quizzes():
    """Students only ever see published quizzes; admins see everything
    (optionally filtered) so they can manage drafts too."""
    db = get_supabase()
    query = db.table("quizzes").select("*")

    if g.user_role != "ADMIN":
        query = query.eq("status", "PUBLISHED")
    else:
        status = request.args.get("status")
        if status:
            query = query.eq("status", status)

    category_id = request.args.get("category_id")
    if category_id:
        query = query.eq("category_id", category_id)

    search = request.args.get("search")
    if search:
        query = query.ilike("title", f"%{search}%")

    result = query.order("created_at", desc=True).execute()
    return jsonify(result.data)


@quizzes_bp.get("/<quiz_id>")
@login_required
def get_quiz(quiz_id):
    db = get_supabase()
    result = db.table("quizzes").select("*").eq("id", quiz_id).execute()
    if not result.data:
        return jsonify({"error": "Quiz not found"}), 404

    quiz = result.data[0]
    if g.user_role != "ADMIN" and quiz["status"] != "PUBLISHED":
        return jsonify({"error": "Quiz not found"}), 404

    return jsonify(quiz)


@quizzes_bp.post("")
@admin_required
def create_quiz():
    data = request.get_json(silent=True) or {}
    required = ("title", "duration_minutes")
    if any(not data.get(f) for f in required):
        return jsonify({"error": f"Required fields: {', '.join(required)}"}), 400

    db = get_supabase()
    payload = {
        "title": data["title"],
        "description": data.get("description"),
        "category_id": data.get("category_id"),
        "difficulty": data.get("difficulty"),
        "duration_minutes": data["duration_minutes"],
        "passing_score": data.get("passing_score", 60),
        "max_attempts": data.get("max_attempts", 1),
        "status": "DRAFT",
        "thumbnail_url": data.get("thumbnail_url"),
        "negative_marks": data.get("negative_marks", 0),
        "randomize_questions": bool(data.get("randomize_questions", False)),
        "randomize_options": bool(data.get("randomize_options", False)),
        "created_by": g.user_id,
    }
    result = db.table("quizzes").insert(payload).execute()
    return jsonify(result.data[0]), 201


@quizzes_bp.put("/<quiz_id>")
@admin_required
def update_quiz(quiz_id):
    data = request.get_json(silent=True) or {}
    allowed_fields = (
        "title", "description", "category_id", "difficulty",
        "duration_minutes", "passing_score", "max_attempts", "thumbnail_url",
        "negative_marks", "randomize_questions", "randomize_options",
    )
    allowed = {k: v for k, v in data.items() if k in allowed_fields}
    if not allowed:
        return jsonify({"error": "Nothing to update"}), 400

    db = get_supabase()
    result = db.table("quizzes").update(allowed).eq("id", quiz_id).execute()
    if not result.data:
        return jsonify({"error": "Quiz not found"}), 404
    return jsonify(result.data[0])


@quizzes_bp.delete("/<quiz_id>")
@admin_required
def delete_quiz(quiz_id):
    db = get_supabase()
    db.table("quizzes").delete().eq("id", quiz_id).execute()
    return jsonify({"message": "Quiz deleted"})


@quizzes_bp.patch("/<quiz_id>/publish")
@admin_required
def publish_quiz(quiz_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "PUBLISHED")
    if status not in ("DRAFT", "PUBLISHED", "UNPUBLISHED"):
        return jsonify({"error": "Invalid status"}), 400

    db = get_supabase()

    if status == "PUBLISHED":
        questions = db.table("questions").select("id").eq("quiz_id", quiz_id).execute()
        if not questions.data:
            return jsonify({"error": "Cannot publish a quiz with no questions"}), 400

    result = db.table("quizzes").update({"status": status}).eq("id", quiz_id).execute()
    if not result.data:
        return jsonify({"error": "Quiz not found"}), 404
    return jsonify(result.data[0])
