from flask import Blueprint, request, jsonify
from extensions import get_supabase
from utils.auth_decorators import login_required

leaderboard_bp = Blueprint("leaderboard", __name__, url_prefix="/api/leaderboard")


@leaderboard_bp.get("")
@login_required
def get_leaderboard():
    """Ranks students by average score across their completed attempts.
    Optional ?category_id= to scope to quizzes in one category."""
    db = get_supabase()
    category_id = request.args.get("category_id")

    attempts_query = db.table("attempts").select("user_id,percentage,quiz_id").eq("status", "COMPLETED")
    attempts = attempts_query.execute().data

    if category_id:
        quiz_ids_in_category = {
            q["id"] for q in db.table("quizzes").select("id").eq("category_id", category_id).execute().data
        }
        attempts = [a for a in attempts if a["quiz_id"] in quiz_ids_in_category]

    stats_by_user = {}
    for a in attempts:
        s = stats_by_user.setdefault(a["user_id"], {"total": 0.0, "count": 0})
        s["total"] += a["percentage"] or 0
        s["count"] += 1

    users_by_id = {u["id"]: u for u in db.table("users").select("id,name").eq("role", "STUDENT").execute().data}

    leaderboard = []
    for user_id, s in stats_by_user.items():
        user = users_by_id.get(user_id)
        if not user:
            continue
        leaderboard.append({
            "user_id": user_id,
            "name": user["name"],
            "average_score": round(s["total"] / s["count"], 2),
            "quizzes_completed": s["count"],
        })

    leaderboard.sort(key=lambda r: r["average_score"], reverse=True)
    for i, row in enumerate(leaderboard, start=1):
        row["rank"] = i

    return jsonify(leaderboard)
