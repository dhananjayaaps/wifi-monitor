"""Authentication routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...schemas.user import RegisterUserRequest, LoginRequest
from ...services import auth_service


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    data = RegisterUserRequest(**payload)
    try:
        user = auth_service.register_user(email=data.email, password=data.password)
    except auth_service.AuthError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    return jsonify({"status": "success", "data": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    data = LoginRequest(**payload)
    try:
        token = auth_service.authenticate(email=data.email, password=data.password)
    except auth_service.AuthError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 401
    return jsonify({"status": "success", "access_token": token})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = auth_service.get_user(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "success", "data": user.to_dict()})
