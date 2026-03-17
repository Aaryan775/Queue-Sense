# =============================================
# QueueSense - Settings API Routes
# =============================================
# This module handles global system configuration
# including general, notification, security, and system settings.
# =============================================

from flask import Blueprint, request, jsonify
from .. import db
from ..models import SystemSettings
from ..utils.decorators import token_required, admin_required

settings_bp = Blueprint('settings', __name__)

# =============================================
# ROUTE: Get All Settings
# GET /api/settings
# =============================================
@settings_bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_settings(current_user):
    """Get all system settings."""
    settings = SystemSettings.query.all()
    # If no settings exist yet, return empty dict or defaults
    return jsonify({
        'settings': {s.setting_key: s.setting_value for s in settings}
    }), 200

# =============================================
# ROUTE: Update Settings (Bulk)
# POST /api/settings
# =============================================
@settings_bp.route('/', methods=['POST'])
@token_required
@admin_required
def update_settings(current_user):
    """Bulk update or create settings."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    updated_keys = []
    for key, value in data.items():
        setting = SystemSettings.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = str(value)
        else:
            setting = SystemSettings(setting_key=key, setting_value=str(value))
            db.session.add(setting)
        updated_keys.append(key)

    db.session.commit()
    return jsonify({
        'message': 'Settings updated successfully',
        'updated_keys': updated_keys
    }), 200

# =============================================
# ROUTE: Update Single Setting
# PUT /api/settings/<key>
# =============================================
@settings_bp.route('/<key>', methods=['PUT', 'POST'])
@token_required
@admin_required
def update_single_setting(current_user, key):
    """Update a specific setting by key."""
    data = request.get_json()
    value = data.get('value')
    
    if value is None:
        return jsonify({'error': 'No value provided'}), 400

    setting = SystemSettings.query.filter_by(setting_key=key).first()
    if setting:
        setting.setting_value = str(value)
    else:
        setting = SystemSettings(setting_key=key, setting_value=str(value))
        db.session.add(setting)

    db.session.commit()
    return jsonify({
        'message': f'Setting {key} updated',
        'key': key,
        'value': value
    }), 200

# =============================================
# ROUTE: Reset System Data (Admin)
# POST /api/settings/reset
# =============================================
@settings_bp.route('/reset', methods=['POST'])
@token_required
@admin_required
def reset_system(current_user):
    """Reset system data (delete all tokens, appointments)."""
    try:
        from ..models import QueueElder, QueueNormal, Appointment
        QueueElder.query.delete()
        QueueNormal.query.delete()
        Appointment.query.delete()
        db.session.commit()
        return jsonify({'message': 'System data reset successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# =============================================
# ROUTE: Export Backup (Admin)
# GET /api/settings/backup
# =============================================
@settings_bp.route('/backup', methods=['GET'])
@token_required
@admin_required
def export_backup(current_user):
    """Simulate a system backup export."""
    from datetime import datetime
    # In a real app, this would generate a SQL dump or JSON export
    return jsonify({
        'message': 'Backup generated successfully',
        'timestamp': datetime.utcnow().isoformat(),
        'download_url': '#backup-link'
    }), 200
