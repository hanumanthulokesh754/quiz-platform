from flask import Flask, jsonify
from flask_cors import CORS
from config import Config

from routes.auth import auth_bp
from routes.users import users_bp
from routes.categories import categories_bp
from routes.quizzes import quizzes_bp
from routes.questions import questions_bp
from routes.attempts import attempts_bp
from routes.admin import admin_bp
from routes.leaderboard import leaderboard_bp


def create_app():
    app = Flask(__name__)
    CORS(app, origins=[Config.FRONTEND_ORIGIN] if Config.FRONTEND_ORIGIN != "*" else "*")

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(attempts_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(leaderboard_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def server_error(e):
        # Secure error handling: never leak stack traces / internals to the client.
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
