import cv2 as cv
import numpy as np 
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose 
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


# test1 = '/Users/charlie/Desktop/test1.mp4'
# test2 = '/Users/charlie/Desktop/test2.mp4'

# cap = cv.VideoCapture(test1)

count = 0
direction = "down" # either "down", or "fix"
cooldown_duration = 20  # Cooldown duration in frames (adjust as needed)
cooldown_timer = 0

font = cv.FONT_HERSHEY_SIMPLEX
org = (25, 25) 
font_scale = 2
color = (255, 255, 255)  
thickness = 2
line_type = cv.LINE_AA

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    ba = a - b
    bc = c - b

    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cos_angle)

    return np.degrees(angle)

def distance(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.linalg.norm(a - b)

def process_frame(frame):
    global direction, count, cooldown_timer
    
    image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

    results = pose.process(image)

    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        landmarks = results.pose_landmarks.landmark

        # check for left side or right side - TODO: same for rightside
        shoulder_left = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, 
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        hip_left = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, 
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
        ankle_left = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, 
                        landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
        elbow_left = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, 
                        landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
        wrist_left = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, 
                        landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
        shoulder_right = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, 
                        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        hip_right = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                        landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
        ankle_right = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, 
                        landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
        elbow_right = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x, 
                        landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
        wrist_right = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, 
                        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

        plank_angle_left = calculate_angle(shoulder_left, hip_left, ankle_left)
        elbow_angle_left = calculate_angle(shoulder_left, elbow_left, wrist_left)
        plank_angle_right = calculate_angle(shoulder_right, hip_right, ankle_right)
        elbow_angle_right = calculate_angle(shoulder_right, elbow_right, wrist_right)

        in_plank_position = (((160 < plank_angle_left) and (plank_angle_left <= 185)) or 
                            ((160 < plank_angle_right) and (plank_angle_right <= 185)))
        shoulders_above_elbows = (elbow_angle_left > 90) and (elbow_angle_right > 90)

        if cooldown_timer == 0:
            if in_plank_position:
                if shoulders_above_elbows and direction == "up":
                    count += 0.5
                    direction = "down"
                        
                elif (not shoulders_above_elbows) and direction == "down":
                    count += 0.5
                    direction = "up"
                    

        cv.putText(image, "Push-up count: " + str(count), org, font, font_scale, color, thickness, line_type)
                
                
        if cooldown_timer > 0:
            cooldown_timer -= 1

    return image