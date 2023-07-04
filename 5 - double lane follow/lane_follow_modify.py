import cv2
import numpy as np
# import logging
import math
import time
from picarx import Picarx

px = Picarx()

# acquisizione video dalla webcam (0)
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

# video locale
#cap = cv2.VideoCapture()

def detect_edges(frame):
    #hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    #lower_blue = np.array([0, 0, 0])
    #upper_blue = np.array([20, 20, 20])
    #mask = cv2.inRange(hsv, lower_blue, upper_blue)
    edges = cv2.Canny(frame, 180, 280)
    # visualizzazione del frame acquisito
    return edges

off_set_region = 20

def region_of_interest(edges):
    height, width = 480,360
    mask = np.zeros_like(edges)
    
    # only focus bottom half of the screen
    polygon = np.array([[
        (0, 140 ),
        (width, 140 ),
        (width, height),
        (0, height),
    ]], np.int32)

    cv2.fillPoly(mask, polygon, 255)
    cropped_edges = cv2.bitwise_and(edges, mask)
    return cropped_edges

# function to detect lines

def detect_line_segments(cropped_edges):
    # tuning min_threshold, minLineLength, maxLineGap is a trial and error process by hand
    rho = 1  # distance precision in pixel, i.e. 1 pixel
    angle = np.pi / 180  # angular precision in radian, i.e. 1 degree
    min_threshold = 15  # minimal of votes
    line_segments = cv2.HoughLinesP(cropped_edges, rho, angle, min_threshold, 
                                    np.array([]), minLineLength=10, maxLineGap=5)

    return line_segments

def average_slope_intercept(frame, line_segments):
    """
    This function combines line segments into one or two lane lines
    If all line slopes are < 0: then we only have detected left lane
    If all line slopes are > 0: then we only have detected right lane
    """
    
    
    lane_lines = []
    if line_segments is None:
        #logging.info('No line_segment segments detected')
        return lane_lines
    height, width, _ = frame.shape
    left_fit = []
    right_fit = []

    boundary = 1/3
    left_region_boundary = width * (1 - boundary)  # left lane line segment should be on left 1/2 of the screen
    right_region_boundary = width * boundary # right lane line segment should be on left 1/2 of the screen
    
    #print(left_region_boundary,right_region_boundary)
    
    for line_segment in line_segments:
        for x1, y1, x2, y2 in line_segment:
            if x1 == x2:
                #logging.info('skipping vertical line segment (slope=inf): %s' % line_segment)
                continue
            fit = np.polyfit((x1, x2), (y1, y2), 1)
            slope = fit[0]
            intercept = fit[1]
            if slope < 0:
                if x1 < left_region_boundary and x2 < left_region_boundary:
                    left_fit.append((slope, intercept))
            else:
                if x1 > right_region_boundary and x2 > right_region_boundary:
                    right_fit.append((slope, intercept))

    left_fit_average = np.average(left_fit, axis=0)
    if len(left_fit) > 0:
        lane_lines.append(make_points(frame, left_fit_average))

    right_fit_average = np.average(right_fit, axis=0)
    if len(right_fit) > 0:
        lane_lines.append(make_points(frame, right_fit_average))

    #logging.debug('lane lines: %s' % lane_lines)  # [[[316, 720, 484, 432]], [[1009, 720, 718, 432]]]

    return lane_lines


def make_points(frame, line):
    height, width, _ = frame.shape
    slope, intercept = line
    y1 = height  # bottom of the frame
    y2 = int(y1 * 1 / 2)  # make points from middle of the frame down

    # bound the coordinates within the frame
    x1 = max(-width, min(2 * width, int((y1 - intercept) / slope)))
    x2 = max(-width, min(2 * width, int((y2 - intercept) / slope)))
    return [[x1, y1, x2, y2]]


def detect_lane(frame):
    
    edges = detect_edges(frame)
    cropped_edges = region_of_interest(edges)
    line_segments = detect_line_segments(cropped_edges)
    #print("lin",line_segments)
    lane_lines = average_slope_intercept(frame, line_segments)
    
    return lane_lines
    #return cropped_edges

def display_lines(frame, lines, line_color=(0, 255, 0), line_width=2):
    line_image = np.zeros_like(frame)
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), line_color, line_width)
    line_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)
    return line_image

def display_heading_line(frame, steering_angle, line_color=(0, 0, 255), line_width=5 ):
    heading_image = np.zeros_like(frame)
    height, width, _ = frame.shape

    # figure out the heading line from steering angle
    # heading line (x1,y1) is always center bottom of the screen
    # (x2, y2) requires a bit of trigonometry

    # Note: the steering angle of:
    # 0-89 degree: turn left
    # 90 degree: going straight
    # 91-180 degree: turn right 
    steering_angle_radian = steering_angle / 180.0 * math.pi
    x1 = int(width / 2)
    y1 = height
    x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
    y2 = int(height / 2)

    cv2.line(heading_image, (x1, y1), (x2, y2), line_color, line_width)
    heading_image = cv2.addWeighted(frame, 0.8, heading_image, 1, 1)

    return heading_image


def stabilize_steering_angle(
          curr_steering_angle, 
          new_steering_angle, 
          num_of_lane_lines, 
          max_angle_deviation_two_lines=1, 
          max_angle_deviation_one_lane=5):
    """
    Using last steering angle to stabilize the steering angle
    if new angle is too different from current angle, 
    only turn by max_angle_deviation degrees
    """

    if num_of_lane_lines == 2 :
        # if both lane lines detected, then we can deviate more
        max_angle_deviation = max_angle_deviation_two_lines
    else :
        # if only one lane detected, don't deviate too much
        max_angle_deviation = max_angle_deviation_one_lane
    
    angle_deviation = new_steering_angle - curr_steering_angle
    if abs(angle_deviation) > max_angle_deviation:
        stabilized_steering_angle = int(curr_steering_angle
            + max_angle_deviation * angle_deviation / abs(angle_deviation))
    else:
        stabilized_steering_angle = new_steering_angle
    return stabilized_steering_angle

# loop finché non viene premuto il tasto "q"

steering_angle = 90
pi_angle = 0

n = 0
x_adjust_2lanes = 1
x_adjust_1lane = 1

while True:
    # acquisizione di un singolo frame dalla cattura video
    ret, frame = cap.read()

    lane_lines = detect_lane(frame)
    #cv2.imshow("lane lines", lane_lines)
    
    lane_lines_image = display_lines(frame, lane_lines)
    #cv2.imshow("lane lines", lane_lines_image)
    
    
    num_lanes = len(lane_lines)
    
    # 2 casi
    # caso in cui ci sono 2 linee
    
    if num_lanes == 2:
        print("2lines ")
        # estraggo l'x della linea massima
        _, _, left_x2, _ = lane_lines[0][0]
        _, _, right_x2, _ = lane_lines[1][0]
        #print(left_x2,right_x2) #--> valore x dell'apice delle due line
    
        # calcolo il punto medio "ideale"
        mid = 140 #width/2 = 240/2 = 120

        # calcolo l'offset => di quanto il punto medio tra le linee è spostato rispetto alla metà 
        x_offset = ((left_x2 + right_x2) / 2 - mid)
        y_offset = 270 * 2 # height/2 + offset = 360/2 + 90 = 270

        # calcolo angolo di curavatura
        angle = math.atan(x_offset / y_offset)
        angle_in_deg = int(angle * 180.0 / math.pi)
        
        steering_angle = angle_in_deg +90
        
        #print(left_x2,right_x2,mid,angle_in_deg, steering_angle)
        
        
        heading_image = display_heading_line(lane_lines_image, steering_angle)
        
        cv2.imshow("lane lines", heading_image)
         
        
        
        if n > 200:
            px.set_dir_servo_angle(angle_in_deg)
            px.forward(0.1)
            #time.sleep(0.075)
            #px.forward(0)
         
        
    elif num_lanes == 1:
        px.forward(0)
        print("1 line")
        x1, _, x2, _ = lane_lines[0][0]
        x_offset = (x2 - x1)
        y_offset = 270

        # calcolo angolo di curavatura
        angle = math.atan(x_offset / y_offset)
        angle_in_deg = int(angle * 180.0 / math.pi) # angolo del pi
    
        steering_angle = angle_in_deg +90
        
        #print(x1,x2,angle_in_deg, steering_angle)
        
        
        heading_image = display_heading_line(lane_lines_image, steering_angle)
        
        cv2.imshow("lane lines", heading_image)
        
        #time_wait = abs(angle_in_deg/10)
        print(angle_in_deg)
        
            
        
        if n > 200:
            px.forward(0)
            if angle_in_deg < 0:                   
                px.set_dir_servo_angle(-25)
                px.forward(0.1)
                time.sleep(0.12)
            else:
                px.set_dir_servo_angle(25)
                px.forward(0.1)
                time.sleep(0.12)
            
            px.forward(0)
            px.set_dir_servo_angle(0)
            
            '''
            if angle_in_deg > 20:
                #angle_in_deg = 20
                #time.sleep(0.2)
                while(angle_in_deg > 0):
                    px.forward(0)
                    px.set_dir_servo_angle(2)
                    angle_in_deg -= 2
                    px.forward(0.1)
                    px.set_dir_servo_angle(0)
                    
            elif angle_in_deg < -20:
                #angle_in_deg = -20
                #time.sleep(0.2)
                while(angle_in_deg < 0): 
                    px.forward(0)
                    px.set_dir_servo_angle(-2)
                    angle_in_deg +=2
                    px.forward(0.1)
                    px.set_dir_servo_angle(0)
            else:
                px.set_dir_servo_angle(0)
            '''                 
         

    # attesa di 1 millisecondo, finché non viene premuto il tasto "q"
    
    else:

        print("problem : no lines detected!! ")
        angle_value_pi = 0
        px.forward(0)
        cv2.imshow("lane lines", frame)
    
    if cv2.waitKey(1) == ord('q'):

        px.forward(0)

        break
    #time.sleep(1)
    
    n += 1
    


# rilascio della cattura video e chiusura della finestra
cap.release()
cv2.destroyAllWindows()
