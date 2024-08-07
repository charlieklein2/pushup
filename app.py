import base64
from flask import Flask, redirect, render_template, Response, request, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
import numpy as np
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt 
from dotenv import load_dotenv
import os

import cv2 as cv
from pushup import process_frame

app = Flask(__name__)

load_dotenv()
sql_key = os.getenv('key')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = sql_key
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_viewq = "login"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    count = db.Column(db.Integer, default=0)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        
        if existing_user_username:
            raise ValidationError("That username already exists. Please choose a different one.")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")

@app.route('/current_user', methods=['GET'])
@login_required
def get_current_user():
    user_data = {
        'username': current_user.username,
        'count': current_user.count
    }
    return jsonify(user_data)


@app.route('/users', methods=['GET'])
@login_required
def get_users():
    users = User.query.order_by(User.count.desc()).limit(10).all()
    users_list = [{'username': user.username, 'count': user.count} for user in users]
    return jsonify(users_list)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('about'))

    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/live-feed')
@login_required
def live_feed():
    return render_template('live-feed.html')

@app.route('/process_frame', methods=['POST'])
def generate_frames():
    frame = receive_frame()
    if frame is None:
        return jsonify({'error': 'Invalid frame'}), 400
    
    user = db.session.get(User, current_user.id)
    user_count = user.count
    local_count = request.json.get('count', 0)

    processed_frame, local_count, user_count = process_frame(frame, local_count, user_count)

    user.count = user_count
    db.session.commit()

    # Encode the processed frame as JPEG
    ret, buffer = cv.imencode('.jpg', processed_frame)
    if not ret:
        return jsonify({'error': 'Failed to encode frame'}), 500

    response_image = base64.b64encode(buffer).decode('utf-8')
    return jsonify({'image': response_image, 'local_count': local_count, 'user_count': user_count})
    
    """
    local_count = 0
    

    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Could not start camera.")

    while True:
        success, frame = cap.read()
        if not success:
            break
        with app.app_context():
        # Process the frame using your model
            user = db.session.get(User, user_id)
            user_count = user.count
            
            processed_frame, local_count, user_count = process_frame(frame, local_count, user_count)

            user.count = user_count
            db.session.commit()

        # Encode the processed frame as JPEG
        ret, buffer = cv.imencode('.jpg', processed_frame)
        if not ret:
            continue

        frame = buffer.tobytes()
 
        try:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except (GeneratorExit, BrokenPipeError):
            print("Client disconnected or broken pipe")
            cap.release()
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            cap.release()
            break"""

"""@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(current_user.id), mimetype='multipart/x-mixed-replace; boundary=frame')
"""
# no harm, no foul
def receive_frame():
    data = request.json
    if not data or 'image' not in data:
        return None

    image_data = data['image']
    image_data = image_data.split(',')[1]
    image = base64.b64decode(image_data)
    nparr = np.frombuffer(image, np.uint8)
    frame = cv.imdecode(nparr, cv.IMREAD_COLOR)
    
    return frame

if __name__ == '__main__':
    app.run(debug=True)