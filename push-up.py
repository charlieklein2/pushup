import cv2 as cv
import numpy as np 
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose 

count = 0
position = None

cooldown_duration = 15  # Cooldown duration in frames (adjust as needed)
cooldown_timer = 0

total_frames = 0

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

test1 = '/Users/charlie/Desktop/test1.mp4'
test2 = '/Users/charlie/Desktop/test2.mp4'

cap = cv.VideoCapture(test1)

# can change confidence levels later
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            print("No Camera or end of video")
            break
    
        image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = pose.process(image)

        coords = []

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            landmarks = results.pose_landmarks.landmark

            # check for left side or right side - TODO: same for rightside
            shoulder_left = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, 
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y,
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].z]
            hip_left = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, 
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y, 
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].z]
            ankle_left = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, 
                          landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y, 
                          landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].z]
            elbow_left = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, 
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y,
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].z]
            wrist_left = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, 
                          landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y, 
                          landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].z]

            plank_angle = calculate_angle(shoulder_left, hip_left, ankle_left)
            elbow_angle = calculate_angle(shoulder_left, elbow_left, wrist_left)

            in_plank_position = (165 <= plank_angle) and (plank_angle <= 185)

            if cooldown_timer == 0:
                if in_plank_position:
                    if shoulder_left[1] >= elbow_left[1]:
                        position = "down"
                    if shoulder_left[1] <= elbow_left[1] and position == "down":
                        position = "up"
                        count += 1
                        print(count)
                        cooldown_timer = cooldown_duration

            if cooldown_timer > 0:
                cooldown_timer -= 1
            

            """
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            for id, im in enumerate(results.pose_landmarks.landmark):
                height, width, _ = image.shape
                x, y = int(im.x * width), int(im.y * height)
                coords.append([id, x, y])

            # 11 & 12 are shoulder points and 13 & 14 are elbow points.  
            # to do from here: make the logic here more robust               
            if len(coords) != 0: 
                if coords[12][2] >= coords[14][2] and coords[11][2] >= coords[13][2]:
                    position = "down"
                if coords[12][2] <= coords[14][2] and coords[11][2] <= coords[13][2] and  position == "down":
                    position = "up"
                    count += 1
                    print(count)
            """


        cv.imshow('frame', image)
        if cv.waitKey(10) & 0xFF == ord('q'):
            break
 
cap.release()
cv.destroyAllWindows()

print("Total pushups detected: " + str(count))
