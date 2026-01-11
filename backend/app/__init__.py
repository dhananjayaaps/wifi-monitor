"""Application factory for the backend service."""
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from pydantic import ValidationError
from .config.settings import get_settings
from .extensions import db, jwt, cors
from .api import init_api


def create_app() -> Flask:
	settings = get_settings()

	app = Flask(__name__)
	app.config.update(
		SECRET_KEY=settings.secret_key,
		JWT_SECRET_KEY=settings.jwt_secret_key,
		SQLALCHEMY_DATABASE_URI=settings.database_url,
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
	)

	cors.init_app(app, resources={r"/*": {"origins": settings.cors_origins}})
	db.init_app(app)
	jwt.init_app(app)

	register_error_handlers(app)
	init_api(app, prefix=settings.api_prefix)

	with app.app_context():
		db.create_all()

	return app


def register_error_handlers(app: Flask) -> None:
	@app.errorhandler(404)
	def not_found(error):
		return jsonify({"status": "error", "message": "Not found"}), 404

	@app.errorhandler(400)
	def bad_request(error):
		return jsonify({"status": "error", "message": "Bad request"}), 400

	@app.errorhandler(500)
	def server_error(error):
		return jsonify({"status": "error", "message": "Internal server error"}), 500

	@app.errorhandler(ValidationError)
	def validation_error(error):
		return jsonify({"status": "error", "message": "Validation failed", "details": error.errors()}), 400
