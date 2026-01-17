"""Agent endpoints for Pi-agent device sync and usage ingestion."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from datetime import datetime
from ...extensions import db
from ...models import Agent, Device, DeviceStat

agents_bp = Blueprint("agents", __name__)


def agent_required(f):
    """Decorator to require agent API key authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-Agent-API-Key")
        if not api_key:
            return jsonify({"status": "error", "message": "Missing API key"}), 401
        
        agent = Agent.query.filter_by(api_key=api_key, is_active=True).first()
        if not agent:
            return jsonify({"status": "error", "message": "Invalid API key"}), 401
        
        # Update last sync time
        agent.last_sync = datetime.utcnow()
        db.session.commit()
        
        # Pass agent to the route
        return f(agent=agent, *args, **kwargs)
    return decorated


@agents_bp.route("/register", methods=["POST"])
@jwt_required()
def register_agent():
    """Register a new Pi agent (requires user auth)."""
    data = request.get_json()
    user_id = int(get_jwt_identity())
    
    name = data.get("name", "Pi Agent")
    
    agent = Agent(
        name=name,
        owner_id=user_id,
        api_key=Agent.generate_api_key(),
        is_active=True
    )
    
    db.session.add(agent)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "data": {
            **agent.to_dict(),
            "api_key": agent.api_key  # Only shown once
        }
    }), 201


@agents_bp.route("/devices", methods=["POST"])
@agent_required
def sync_devices(agent):
    """Sync device list from agent (bulk upsert)."""
    data = request.get_json()
    devices_data = data.get("devices", [])
    
    synced = []
    for dev_data in devices_data:
        mac = dev_data.get("mac_address")
        if not mac:
            continue
        
        device = Device.query.filter_by(mac_address=mac).first()
        if not device:
            device = Device(
                owner_id=agent.owner_id,
                mac_address=mac,
                ip_address=dev_data.get("ip_address"),
                hostname=dev_data.get("hostname"),
                manufacturer=dev_data.get("manufacturer"),
                device_type=dev_data.get("device_type"),
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                is_active=True
            )
            db.session.add(device)
        else:
            # Update existing
            device.ip_address = dev_data.get("ip_address") or device.ip_address
            device.hostname = dev_data.get("hostname") or device.hostname
            device.manufacturer = dev_data.get("manufacturer") or device.manufacturer
            device.device_type = dev_data.get("device_type") or device.device_type
            device.last_seen = datetime.utcnow()
            device.is_active = True
        
        synced.append(mac)
    
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "data": {
            "synced_count": len(synced),
            "synced_macs": synced
        }
    }), 200


@agents_bp.route("/stats", methods=["POST"])
@agent_required
def ingest_stats(agent):
    """Ingest device usage stats from agent (bulk insert)."""
    data = request.get_json()
    stats_data = data.get("stats", [])
    
    ingested = []
    for stat in stats_data:
        mac = stat.get("mac_address")
        if not mac:
            continue
        
        device = Device.query.filter_by(mac_address=mac).first()
        if not device:
            continue  # Skip unknown devices
        
        device_stat = DeviceStat(
            device_id=device.id,
            timestamp=datetime.utcnow(),
            bytes_uploaded=stat.get("bytes_uploaded", 0),
            bytes_downloaded=stat.get("bytes_downloaded", 0)
        )
        db.session.add(device_stat)
        ingested.append(mac)
    
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "data": {
            "ingested_count": len(ingested),
            "ingested_macs": ingested
        }
    }), 201


@agents_bp.route("/ping", methods=["GET"])
@agent_required
def ping(agent):
    """Health check for agent connectivity."""
    return jsonify({
        "status": "success",
        "data": {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "message": "Agent authenticated"
        }
    }), 200
