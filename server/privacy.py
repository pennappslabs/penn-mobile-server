from datetime import datetime

from flask import g, jsonify, request
from sqlalchemy.exc import IntegrityError

from server import app, sqldb
from server.auth import anonymous_auth, auth


class PrivacySetting(sqldb.Model):
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey("account.id"), primary_key=True)
    setting = sqldb.Column(sqldb.VARCHAR(255), primary_key=True)
    enabled = sqldb.Column(sqldb.Boolean)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    updated_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


@app.route("/privacy/settings", methods=["POST"])
@auth()
def save_privacy_settings():
    settings = request.get_json()
    for setting in settings:
        enabled = settings[setting]
        privSetting = PrivacySetting(account=g.account.id, setting=setting, enabled=enabled)
        try:
            sqldb.session.add(privSetting)
            sqldb.session.commit()
        except IntegrityError:
            sqldb.session.rollback()
            privSetting = PrivacySetting.query.filter_by(
                account=g.account.id, setting=setting
            ).first()
            if privSetting.enabled != enabled:
                privSetting.enabled = enabled
                privSetting.updated_at = datetime.now()
                sqldb.session.commit()
    return jsonify({"success": True})


@app.route("/privacy/settings", methods=["GET"])
@auth()
def get_privacy_settings_endpoint():
    jsonArr = get_privacy_settings(g.account)
    return jsonify({"settings": jsonArr})


def get_privacy_settings(account):
    settings = PrivacySetting.query.filter_by(account=account.id).all()
    jsonArr = {}
    for setting in settings:
        jsonArr[setting.setting] = setting.enabled
    return jsonArr


@app.route("/privacy/anonymous/register", methods=["POST"])
@anonymous_auth
def register_device_key_password_hash():
    return jsonify({"success": True})
