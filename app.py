from flask import Flask, render_template, Response
import cv2 as cv
from flask_socketio import SocketIO, emit
import base64
import numpy as np

from pushup import process_frame

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/live-feed')
def live_feed():
    return render_template('live-feed.html')

@socketio.on('video_frame')
def handle_video_frame(data):
    # Decode the image from base64
    frame = base64.b64decode(data.split(',')[1])
    np_frame = np.frombuffer(frame, dtype=np.uint8)
    img = cv.imdecode(np_frame, cv.IMREAD_COLOR)
    
    # Process the frame with your pushup counter logic
    processed_frame = process_frame(img)
    
    # Encode the processed frame back to base64 to send to the client
    _, buffer = cv.imencode('.jpg', processed_frame)
    encoded_img = base64.b64encode(buffer).decode('utf-8')
    emit('processed_frame', {'image': 'data:image/jpeg;base64,' + encoded_img})

if __name__ == '__main__':
    #app.run(debug=True)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)