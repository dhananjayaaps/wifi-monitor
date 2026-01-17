"""Application factory for the backend service."""
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from pydantic import ValidationError
# Use hardcoded settings for local runs (no external config required)
from .extensions import db, jwt, cors
from .api import init_api


def create_app() -> Flask:
	# Hardcoded configuration (development / demo mode)
	class _S:
		secret_key = "dev-secret-key"
		jwt_secret_key = "dev-jwt-secret"
		# store sqlite DB in backend folder for easy local runs
		database_url = "sqlite:///./wifi_monitor.db"
		cors_origins = "*"
		api_prefix = "/api/v1"

	settings = _S()

	app = Flask(__name__)
	app.config.update(
		SECRET_KEY=settings.secret_key,
		JWT_SECRET_KEY=settings.jwt_secret_key,
		SQLALCHEMY_DATABASE_URI=settings.database_url,
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
	)

	# Configure CORS FIRST to handle preflight requests properly
	cors.init_app(
		app,
		resources={
			r"/*": {
				"origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
				"methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
				"allow_headers": ["Content-Type", "Authorization", "Accept"],
				"expose_headers": ["Content-Type", "Authorization"],
				"supports_credentials": True,
				"max_age": 3600
			}
		}
	)
	
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
