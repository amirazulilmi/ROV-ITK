from flask import Flask
from flask import render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = 'your secret here'
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index2.html')


@socketio.on('stick')
def handle_stick(data):
    print(data)


if __name__ == '__main__':
    socketio.run(app)
