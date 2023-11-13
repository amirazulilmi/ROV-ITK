import time
import serial
import numpy as np
import matplotlib.pyplot as plt
import cv2
from threading import Lock
from flask import Flask, render_template, session, request, \
    copy_current_request_context, Response
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask_serial import Serial

async_mode = None

app = Flask(__name__)
# app.config['SERIAL_TIMEOUT'] = 0.2
# app.config['SERIAL_PORT'] = 'COM2'
# app.config['SERIAL_BAUDRATE'] = 115200
# app.config['SERIAL_BYTESIZE'] = 8
# app.config['SERIAL_PARITY'] = 'N'
# app.config['SERIAL_STOPBITS'] = 1


# ser = Serial(app)
ser = serial.Serial('COM6', 115200, timeout=1)

ser.reset_input_buffer()
print ('Arduino connected')

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


@socketio.on('stick')
def handle_stick(data):
    print(data)


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count})


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


@app.route('/joy')
def joy():
    return render_template('joygamepad.html', async_mode=socketio.async_mode)


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.event
def my_broadcast_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)
    print('ini gerak ' + message['data'])

    if message['data'] == 'Maju':
        print("kirim maju")
        ser.write(b'W 1880 1880;')
        line = ser.readline()
        print(line)
    
    elif message['data'] =='Mundur':
        print("kirim mundur")
        ser.write(b'S 1720 1720;')
        line = ser.readline()
        print(line)
                  
    elif message['data'] =='Kiri':
        print("kirim kiri")
        ser.write(b'A 1780 1820;')
        line = ser.readline()
        print(line)
            
    elif message['data'] =='Kanan':
        print("kirim kanan")
        ser.write(b'D 1820 1780;')
        line = ser.readline()
        print(line)
        
    elif message['data'] =='Naik':
        print("kirim naik")
        ser.write(b'Q 1880 1880;')
        line = ser.readline()
        print(line)       
    
    elif message['data'] =='Turun':
        print("kirim turun")
        ser.write(b'E 1720 1720;')
        line = ser.readline()
        print(line)
            
    elif message['data'] == 'Stop':
        print("Stop")
        ser.write(b'K ;')
        line = ser.readline()
        print(line)
        
    elif message['data'] == 'StopHorizontal':
        print("StopH")
        ser.write(b'KH ;')
        line = ser.readline()
        print(line)
        
    elif message['data'] == 'StopVertikal':
        print("StopV")
        ser.write(b'KV ;')
        line = ser.readline()
        print(line)

@socketio.event
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         to=message['room'])
    close_room(message['room'])


@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         to=message['room'])


@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.event
def my_ping():
    emit('my_pong')


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)


# setup camera and resolution
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


def gather_img():
    while True:
        time.sleep(0.05)
        _, img = cam.read()
        _, frame = cv2.imencode('.jpg', img)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')


@app.route("/mjpeg")
def mjpeg():
    return Response(gather_img(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    socketio.run(app, debug=False)
