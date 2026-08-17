from flask import Blueprint, request, jsonify
from extensions import get_supabase
from utils.auth_decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/attempts")
@admin_required
def list_all_attempts():
    db = get_supabase()
    query = db.table("attempts").select("*, quizzes(title), users(name,email)")

    quiz_id = request.args.get("quiz_id")
    if quiz_id:
        query = query.eq("quiz_id", quiz_id)
    user_id = request.args.get("user_id")
    if user_id:
        query = query.eq("user_id", user_id)
    status = request.args.get("status")
    if status:
        query = query.eq("status", status)

    result = query.order("started_at", desc=True).execute()
    return jsonify(result.data)


@admin_bp.get("/attempts/<attempt_id>")
@admin_required
def get_attempt_detail(attempt_id):
    db = get_supabase()
    result = db.table("attempts").select("*, quizzes(title), users(name,email)").eq("id", attempt_id).execute()
    if not result.data:
        return jsonify({"error": "Attempt not found"}), 404
    attempt = result.data[0]
    attempt["answers"] = (
        db.table("answers").select("*, questions(question_text)").eq("attempt_id", attempt_id).execute().data
    )
    return jsonify(attempt)


@admin_bp.get("/analytics")
@admin_required
def analytics():
    db = get_supabase()

    total_students = db.table("users").select("id", count="exact").eq("role", "STUDENT").execute().count or 0
    total_quizzes = db.table("quizzes").select("id", count="exact").execute().count or 0
    published_quizzes = (
        db.table("quizzes").select("id", count="exact").eq("status", "PUBLISHED").execute().count or 0
    )
    draft_quizzes = db.table("quizzes").select("id", count="exact").eq("status", "DRAFT").execute().count or 0
    total_questions = db.table("questions").select("id", count="exact").execute().count or 0

    completed_attempts = (
        db.table("attempts").select("percentage").eq("status", "COMPLETED").execute().data
    )
    total_attempts = len(completed_attempts)
    avg_score = (
        round(sum(a["percentage"] or 0 for a in completed_attempts) / total_attempts, 2)
        if total_attempts else 0
    )

    # Pass/fail requires each attempt's quiz passing_score — fetched per-quiz
    # rather than N+1 per-attempt by pulling all quizzes once.
    quizzes_by_id = {q["id"]: q for q in db.table("quizzes").select("id,passing_score").execute().data}
    attempts_full = db.table("attempts").select("quiz_id,percentage").eq("status", "COMPLETED").execute().data
    passed = sum(
        1 for a in attempts_full
        if a["quiz_id"] in quizzes_by_id and (a["percentage"] or 0) >= float(quizzes_by_id[a["quiz_id"]]["passing_score"])
    )
    failed = total_attempts - passed

    return jsonify({
        "total_students": total_students,
        "total_quizzes": total_quizzes,
        "published_quizzes": published_quizzes,
        "draft_quizzes": draft_quizzes,
        "total_questions": total_questions,
        "total_attempts": total_attempts,
        "average_score": avg_score,
        "passed_attempts": passed,
        "failed_attempts": failed,
    })
