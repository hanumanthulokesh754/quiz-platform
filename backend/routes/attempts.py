import datetime
from flask import Blueprint, request, jsonify, g
from extensions import get_supabase
from utils.auth_decorators import login_required
from utils.scoring import calculate_score
from utils.randomization import shuffle_for_attempt

attempts_bp = Blueprint("attempts", __name__, url_prefix="/api")


def _sanitize_question_for_attempt(question, options):
    """Strips is_correct/explanation so students can't read the answer key
    from the network tab while a quiz is in progress."""
    return {
        "id": question["id"],
        "question_text": question["question_text"],
        "marks": question["marks"],
        "options": [{"id": o["id"], "option_text": o["option_text"]} for o in options],
    }


@attempts_bp.post("/quizzes/<quiz_id>/start")
@login_required
def start_attempt(quiz_id):
    db = get_supabase()

    quiz_result = db.table("quizzes").select("*").eq("id", quiz_id).execute()
    if not quiz_result.data or quiz_result.data[0]["status"] != "PUBLISHED":
        return jsonify({"error": "Quiz not available"}), 404
    quiz = quiz_result.data[0]

    # Resume an in-progress attempt if one exists, rather than starting a new one.
    existing = (
        db.table("attempts")
        .select("*")
        .eq("quiz_id", quiz_id)
        .eq("user_id", g.user_id)
        .eq("status", "IN_PROGRESS")
        .execute()
    )
    if existing.data:
        attempt = existing.data[0]
    else:
        completed_count = (
            db.table("attempts")
            .select("id", count="exact")
            .eq("quiz_id", quiz_id)
            .eq("user_id", g.user_id)
            .neq("status", "IN_PROGRESS")
            .execute()
        )
        if (completed_count.count or 0) >= quiz["max_attempts"]:
            return jsonify({"error": "Maximum attempts reached for this quiz"}), 403

        attempt = db.table("attempts").insert({
            "quiz_id": quiz_id,
            "user_id": g.user_id,
            "status": "IN_PROGRESS",
        }).execute().data[0]

    questions = db.table("questions").select("*").eq("quiz_id", quiz_id).execute().data
    for q in questions:
        q["options"] = db.table("options").select("*").eq("question_id", q["id"]).execute().data

    # Shuffle is seeded by attempt id, so a page refresh or resumed attempt
    # sees the exact same order rather than re-randomizing every request.
    ordered = shuffle_for_attempt(
        questions,
        attempt["id"],
        randomize_questions=quiz.get("randomize_questions", False),
        randomize_options=quiz.get("randomize_options", False),
    )
    sanitized = [_sanitize_question_for_attempt(q, q["options"]) for q in ordered]

    started_at = datetime.datetime.fromisoformat(attempt["started_at"].replace("Z", "+00:00"))
    elapsed = (datetime.datetime.now(datetime.timezone.utc) - started_at).total_seconds()
    remaining_seconds = max(0, quiz["duration_minutes"] * 60 - int(elapsed))

    return jsonify({
        "attempt_id": attempt["id"],
        "quiz": {k: quiz[k] for k in ("id", "title", "duration_minutes", "passing_score", "negative_marks")},
        "questions": sanitized,
        "remaining_seconds": remaining_seconds,
    })


@attempts_bp.post("/quizzes/<quiz_id>/submit")
@login_required
def submit_attempt(quiz_id):
    data = request.get_json(silent=True) or {}
    attempt_id = data.get("attempt_id")
    submitted_answers = data.get("answers", {})  # { question_id: option_id }

    if not attempt_id:
        return jsonify({"error": "attempt_id is required"}), 400

    db = get_supabase()
    attempt_result = (
        db.table("attempts").select("*").eq("id", attempt_id).eq("user_id", g.user_id).execute()
    )
    if not attempt_result.data:
        return jsonify({"error": "Attempt not found"}), 404
    attempt = attempt_result.data[0]
    if attempt["status"] != "IN_PROGRESS":
        return jsonify({"error": "This attempt has already been submitted"}), 409

    quiz = db.table("quizzes").select("*").eq("id", quiz_id).execute().data[0]

    started_at = datetime.datetime.fromisoformat(attempt["started_at"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    elapsed_seconds = int((now - started_at).total_seconds())
    time_limit_seconds = quiz["duration_minutes"] * 60
    # Backend is the source of truth for expiry — a late submission is still
    # scored, but time_taken is clamped to the allotted duration.
    time_taken = min(elapsed_seconds, time_limit_seconds)
    expired = elapsed_seconds > time_limit_seconds + 15  # small grace period for network latency

    questions = db.table("questions").select("*").eq("quiz_id", quiz_id).execute().data
    for q in questions:
        q["options"] = db.table("options").select("*").eq("question_id", q["id"]).execute().data

    scoring = calculate_score(
        questions,
        {k: v for k, v in submitted_answers.items()},
        negative_marks=quiz.get("negative_marks", 0),
    )

    answer_rows = [
        {
            "attempt_id": attempt_id,
            "question_id": r["question_id"],
            "selected_option_id": r["selected_option_id"],
            "is_correct": r["is_correct"],
        }
        for r in scoring["per_question_results"]
    ]
    if answer_rows:
        db.table("answers").insert(answer_rows).execute()

    updated = db.table("attempts").update({
        "score": scoring["obtained_marks"],
        "percentage": scoring["percentage"],
        "correct_answers": scoring["correct_answers"],
        "incorrect_answers": scoring["incorrect_answers"],
        "unanswered": scoring["unanswered"],
        "time_taken_seconds": time_taken,
        "status": "EXPIRED" if expired else "COMPLETED",
        "completed_at": now.isoformat(),
    }).eq("id", attempt_id).execute().data[0]

    return jsonify({
        "attempt": updated,
        "passed": scoring["percentage"] >= float(quiz["passing_score"]),
    })


@attempts_bp.get("/attempts")
@login_required
def list_attempts():
    db = get_supabase()
    result = (
        db.table("attempts")
        .select("*, quizzes(title)")
        .eq("user_id", g.user_id)
        .order("started_at", desc=True)
        .execute()
    )
    return jsonify(result.data)


@attempts_bp.get("/attempts/<attempt_id>")
@login_required
def get_attempt(attempt_id):
    db = get_supabase()
    result = db.table("attempts").select("*, quizzes(title, passing_score, negative_marks)").eq("id", attempt_id).execute()
    if not result.data:
        return jsonify({"error": "Attempt not found"}), 404
    attempt = result.data[0]
    if attempt["user_id"] != g.user_id and g.user_role != "ADMIN":
        return jsonify({"error": "Not authorized to view this attempt"}), 403

    # NOTE: the "options!<fk_name>" hint must match Supabase's actual FK
    # constraint name on answers.selected_option_id — check it in the
    # Supabase table editor (Database > answers > foreign keys) and adjust
    # this string if the join errors out.
    answers = (
        db.table("answers")
        .select("*, questions(question_text, explanation), options!answers_selected_option_id_fkey(option_text)")
        .eq("attempt_id", attempt_id)
        .execute()
        .data
    )
    attempt["answers"] = answers
    return jsonify(attempt)
