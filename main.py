import os
import eventlet
eventlet.monkey_patch()

from flask import render_template, request
from flask_socketio import disconnect
from app import create_app, socketio
from app import terminal as term_manager

app = create_app()


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("connect")
def on_connect():
    cols = request.args.get("cols", 80, type=int)
    rows = request.args.get("rows", 24, type=int)
    term_manager.create_session(request.sid, socketio, cols=cols, rows=rows)


@socketio.on("input")
def on_input(data):
    session = term_manager.get_session(request.sid)
    if session:
        session.write(data.get("data", ""))


@socketio.on("resize")
def on_resize(data):
    session = term_manager.get_session(request.sid)
    if session:
        session.resize(data.get("cols", 80), data.get("rows", 24))


@socketio.on("disconnect")
def on_disconnect():
    term_manager.remove_session(request.sid)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host="0.0.0.0", port=port)
