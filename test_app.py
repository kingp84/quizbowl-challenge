from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, async_mode="gevent")

@app.route("/")
def index():
    return "Quizbowl Challenge is running!"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)