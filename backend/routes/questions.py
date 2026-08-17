from flask import Blueprint, request, jsonify, g
from extensions import get_supabase
from utils.auth_decorators import admin_required

questions_bp = Blueprint("questions", __name__, url_prefix="/api")


@questions_bp.get("/quizzes/<quiz_id>/questions")
@admin_required
def list_questions(quiz_id):
    """Admin-only: includes is_correct so the admin can review/edit answers."""
    db = get_supabase()
    questions = db.table("questions").select("*").eq("quiz_id", quiz_id).execute().data
    for q in questions:
        opts = db.table("options").select("*").eq("question_id", q["id"]).execute().data
        q["options"] = opts
    return jsonify(questions)


@questions_bp.post("/quizzes/<quiz_id>/questions")
@admin_required
def create_question(quiz_id):
    data = request.get_json(silent=True) or {}
    question_text = (data.get("question_text") or "").strip()
    options = data.get("options") or []

    if not question_text:
        return jsonify({"error": "question_text is required"}), 400
    if len(options) < 2:
        return jsonify({"error": "At least 2 options are required"}), 400
    if sum(1 for o in options if o.get("is_correct")) != 1:
        return jsonify({"error": "Exactly one option must be marked as correct"}), 400

    db = get_supabase()
    question = db.table("questions").insert({
        "quiz_id": quiz_id,
        "question_text": question_text,
        "marks": data.get("marks", 1),
        "explanation": data.get("explanation"),
        "difficulty": data.get("difficulty"),
    }).execute().data[0]

    option_rows = [
        {"question_id": question["id"], "option_text": o["option_text"], "is_correct": bool(o.get("is_correct"))}
        for o in options
    ]
    inserted_options = db.table("options").insert(option_rows).execute().data

    question["options"] = inserted_options
    return jsonify(question), 201


@questions_bp.put("/questions/<question_id>")
@admin_required
def update_question(question_id):
    data = request.get_json(silent=True) or {}
    db = get_supabase()

    field_updates = {k: v for k, v in data.items() if k in ("question_text", "marks", "explanation", "difficulty")}
    if field_updates:
        db.table("questions").update(field_updates).eq("id", question_id).execute()

    if "options" in data:
        options = data["options"]
        if len(options) < 2 or sum(1 for o in options if o.get("is_correct")) != 1:
            return jsonify({"error": "Provide >=2 options with exactly one marked correct"}), 400
        # Replace all options for this question
        db.table("options").delete().eq("question_id", question_id).execute()
        option_rows = [
            {"question_id": question_id, "option_text": o["option_text"], "is_correct": bool(o.get("is_correct"))}
            for o in options
        ]
        db.table("options").insert(option_rows).execute()

    result = db.table("questions").select("*").eq("id", question_id).execute()
    if not result.data:
        return jsonify({"error": "Question not found"}), 404
    question = result.data[0]
    question["options"] = db.table("options").select("*").eq("question_id", question_id).execute().data
    return jsonify(question)


@questions_bp.delete("/questions/<question_id>")
@admin_required
def delete_question(question_id):
    db = get_supabase()
    db.table("questions").delete().eq("id", question_id).execute()
    return jsonify({"message": "Question deleted"})
