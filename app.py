from flask import Flask, render_template, Response, jsonify
import cv2 as cv
from pushup import process_frame
import eventlet
import eventlet.wsgi
import socket

app = Flask(__name__)

count = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/live-feed')
def live_feed():
    global count
    return render_template('live-feed.html', count=count)

def generate_frames():
    global count
    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Could not start camera.")

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Process the frame using your model
        processed_frame, count = process_frame(frame, count)

        # Encode the processed frame as JPEG
        ret, buffer = cv.imencode('.jpg', processed_frame)
        if not ret:
            continue

        frame = buffer.tobytes()

        try:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except (GeneratorExit, BrokenPipeError, socket.error):
            print("Client disconnected or broken pipe")
            cap.release()
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            cap.release()
            break

@app.route('/get_count')
def get_count():
    global count
    return jsonify({'count': count})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8080)), app)