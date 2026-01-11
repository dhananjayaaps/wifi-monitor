"""API package initializer and blueprint registration."""
from flask import Blueprint
from .routes.auth import auth_bp
from .routes.devices import devices_bp
from .routes.usage import usage_bp
from .routes.alerts import alerts_bp
from .routes.system import system_bp


def init_api(app, prefix: str) -> None:
	api_bp = Blueprint("api", __name__, url_prefix=prefix)

	api_bp.register_blueprint(auth_bp, url_prefix="/auth")
	api_bp.register_blueprint(devices_bp, url_prefix="/devices")
	api_bp.register_blueprint(usage_bp, url_prefix="/usage")
	api_bp.register_blueprint(alerts_bp, url_prefix="/alerts")
	api_bp.register_blueprint(system_bp, url_prefix="/system")

	app.register_blueprint(api_bp)
