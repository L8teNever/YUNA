import os
import eventlet
eventlet.monkey_patch()

from flask import render_template, request, session, jsonify, redirect, url_for
from flask_socketio import emit, disconnect
from app import create_app, socketio
from app import terminal as term_manager

app = create_app()

YUNA_PASSWORD = os.environ.get("YUNA_PASSWORD", "")


def auth_required():
    if not YUNA_PASSWORD:
        return True
    return session.get("authenticated") is True


@app.route("/")
def index():
    if not auth_required():
        return redirect(url_for("login"))
    return render_template("index.html", password_required=bool(YUNA_PASSWORD))


@app.route("/login", methods=["GET", "POST"])
def login():
    if not YUNA_PASSWORD:
        return redirect(url_for("index"))
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if data.get("password") == YUNA_PASSWORD:
            session["authenticated"] = True
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Wrong password"}), 401
    return render_template("index.html", password_required=True)


@app.route("/api/auth-check")
def auth_check():
    return jsonify({"authenticated": auth_required(), "password_required": bool(YUNA_PASSWORD)})


@socketio.on("connect")
def on_connect():
    if not auth_required():
        disconnect()
        return
    cols = request.args.get("cols", 80, type=int)
    rows = request.args.get("rows", 24, type=int)
    term_manager.create_session(request.sid, emit, cols=cols, rows=rows)


@socketio.on("input")
def on_input(data):
    session_obj = term_manager.get_session(request.sid)
    if session_obj:
        session_obj.write(data.get("data", ""))


@socketio.on("resize")
def on_resize(data):
    session_obj = term_manager.get_session(request.sid)
    if session_obj:
        session_obj.resize(data.get("cols", 80), data.get("rows", 24))


@socketio.on("disconnect")
def on_disconnect():
    term_manager.remove_session(request.sid)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host="0.0.0.0", port=port)
