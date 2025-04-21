from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import uuid

app = Flask(_name_)
app.config["SECRET_KEY"] = "your_secret_key"
socketio = SocketIO(app)

active_users = {}  
rooms = {}  

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form["action"]
        username = request.form["username"]
        room = request.form["room"]

        if room not in active_users:
            active_users[room] = []

        # Check if username is already taken in the room
        if username in active_users[room]:
            flash("Username already taken in this room. Choose a different one.", "error")
            return redirect(url_for("index"))

        session["username"] = username
        session["session_id"] = str(uuid.uuid4())  # Unique session ID
        session["room"] = room

        if action == "create":
            rooms[room] = {"name": request.form["room_name"], "users": []}

        return redirect(url_for("chat"))

    return render_template("index.html", rooms=rooms)

@app.route("/chat")
def chat():
    if "username" not in session or "room" not in session:
        return redirect(url_for("index"))
    return render_template("chat.html", username=session["username"], room=session["room"], session_id=session["session_id"])

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    username = data["username"]
    
    join_room(room)

    if room not in active_users:
        active_users[room] = []
    
    if username not in active_users[room]:
        active_users[room].append(username)

    send({"username": "System", "message": f"{username} has joined!"}, to=room)
    emit("update_users", {"users": active_users[room]}, to=room)

@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    username = data["username"]

    leave_room(room)
    if room in active_users and username in active_users[room]:
        active_users[room].remove(username)

    send({"username": "System", "message": f"{username} has left."}, to=room)
    emit("update_users", {"users": active_users[room]}, to=room)

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    send(data, to=room)

@socketio.on("typing")
def handle_typing(data):
    emit("typing", {"username": data["username"]}, to=data["room"])

if _name_ == "_main_":
    socketio.run(app, host="0.0.0.0", port=5005, debug=True)



app.py