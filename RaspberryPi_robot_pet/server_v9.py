import socket
import cv2
import pickle
import numpy as np
import struct
import RPi.GPIO as GPIO
import time
import socket
import os
import math
import threading
import datetime

# Pins for Servos
SERVO_X = 20
SERVO_Z = 21
START_X = 80
START_Z = 20

# Set GPIO numbering mode
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Global for angle value
x_position = START_X
z_position = START_Z

# Set pins 11 & 12 as outputs, and define as PWM servo1 & servo2
GPIO.setup(SERVO_X,GPIO.OUT)
servo_x = GPIO.PWM(SERVO_X,50) # pin 11 for servo_x, pulse 50Hz
GPIO.setup(SERVO_Z,GPIO.OUT)
servo_z = GPIO.PWM(SERVO_Z,50) # pin 12 for servo_z, pulse 50Hz

#RC car base pins
in1 = 5
in2 = 6
en = 13
in3 = 19
in4 = 26 
en2 = 12
temp1=1

# Setting up for Camera View/GUI
width=480
height=320

font = cv2.FONT_HERSHEY_SIMPLEX
scale = 5
color = (0, 0, 255)
thickness = 10

white_img = np.zeros([512,512,3],dtype=np.uint8)
white_img.fill(255)
white_img = cv2.resize(white_img, (width, height))

display = "deactivate"
deactivate_img = cv2.imread("/home/pi/Documents/Capstone/Raspberry-Pi_robot_pet/deactivate.jpg")
follow_img = cv2.imread("/home/pi/Documents/Capstone/Raspberry-Pi_robot_pet/follow_img.jpg")
camera_img = cv2.imread("/home/pi/Documents/Capstone/Raspberry-Pi_robot_pet/camera_img.jpg")
body_img = cv2.imread("/home/pi/Documents/Capstone/Raspberry-Pi_robot_pet/body_img.jpg")

os.system("unclutter -idle 0 &") #Hide mouse pointer

#Set up serial communication w/ Atlas 200DK

UDP_IP = "0.0.0.0" # listen to everything
UDP_PORT = 12345 # port

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((UDP_IP, UDP_PORT))

s.listen(10)
print('Socket now listening')

conn,addr=s.accept()
print(addr)

###########################
### Servo Motor Control ###
###########################

def go_to_angle(servo, angle):
    servo.ChangeDutyCycle(2+(angle/18))
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)
    
def move_up():
    global z_position

    if z_position - 700 > 0:
        z_position = 0
    else:
        z_position = z_position + 5

    go_to_angle(servo_z, z_position)
    
def move_down():
    global z_position
    # Bound z_position
    if z_position - 5 < 0:
        z_position = 0
    else:
        z_position = z_position - 5
    go_to_angle(servo_z, z_position)

def move_left():
    global x_position

    if x_position - 700 > 0:
        x_position = 0
    else:
        x_position = x_position + 5

    go_to_angle(servo_x, x_position)

def move_right():
    global x_position

    if x_position -5 < 0:
        x_position = 0
    else:
        x_position = x_position - 5
        
    go_to_angle(servo_x, x_position)

#############################
### RC Car Control Thread ###
#############################

def RC_car_control():
  global current_hg_command

  while True:
    time.sleep(0.0000000001)

    if current_hg_command == "forwards":
      GPIO.output(in1,GPIO.HIGH)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.HIGH)
      time.sleep(0.5)
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)
      current_hg_command = "send_done_command"

    if current_hg_command == "backwards":
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.HIGH)
      GPIO.output(in3,GPIO.HIGH)
      GPIO.output(in4,GPIO.LOW)
      time.sleep(0.5)
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)
      current_hg_command = "send_done_command"

    elif current_hg_command == "spin_left":
      GPIO.output(in1,GPIO.HIGH)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)
      time.sleep(1)
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)

      current_hg_command = "send_done_command"

    elif current_hg_command == "spin_right":
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.HIGH)
      time.sleep(1)
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)
      current_hg_command = "send_done_command"

    elif current_hg_command == "left":
      GPIO.output(in1,GPIO.HIGH)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)
      time.sleep(0.5)
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)
      current_hg_command = "send_done_command"
    
    elif current_hg_command == "right":
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.HIGH)
      time.sleep(0.5)
      GPIO.output(in1,GPIO.LOW)
      GPIO.output(in2,GPIO.LOW)
      GPIO.output(in3,GPIO.LOW)
      GPIO.output(in4,GPIO.LOW)
      current_hg_command = "send_done_command"
        
###########################

#Initialize serial communication w/ Atlas 200DK
data = b""
payload_size = struct.calcsize(">L")
print("payload_size: {}".format(payload_size))

#Initialize Servo
servo_x.start(0)
servo_z.start(0)

print ("Servo Control Started")

go_to_angle(servo_x, START_X)
go_to_angle(servo_z, START_Z)

#Initialize command SM and mood expression/GUI
global current_hg_command
current_hg_command = "none"

count_forward = 0
count_backward = 0
count_spin = 0
count_takeapicture = 0

count_num = 1 #number of commands in a row sent from Atlas before command is executed

neu_cap = cv2.VideoCapture("./neu.mp4")
# happy_cap = cv2.VideoCapture("./happy.mp4")

cv2.namedWindow('ImageWindow', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('ImageWindow', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

#####################################
### Initialization of RC car base ###
#####################################

GPIO.setmode(GPIO.BCM)
GPIO.setup(in1,GPIO.OUT)
GPIO.setup(in2,GPIO.OUT)
GPIO.setup(en,GPIO.OUT)
GPIO.setup(in3,GPIO.OUT)
GPIO.setup(in4,GPIO.OUT)
GPIO.setup(en2,GPIO.OUT)
GPIO.output(in1,GPIO.LOW)
GPIO.output(in2,GPIO.LOW)
GPIO.output(in3,GPIO.LOW)
GPIO.output(in4,GPIO.LOW)
p=GPIO.PWM(en,1000)
p.start(100)
p2=GPIO.PWM(en2,1000)
p2.start(100)
print("\n")
print("The default speed & direction of motor is LOW & Forward.....")
print("r-run s-stop f-forward b-backward l-low m-medium h-high e-exit")
print("\n")

#RC Car base thread
t1 = threading.Thread(target = RC_car_control,args=())
t1.start()

###########################

while True:
    time.sleep(0.000000000001)
    data = b""

    # Receive data from Atlas 200DK
    while len(data) < payload_size:
        print("Recv: {}".format(len(data)))
        data += conn.recv(4096)

    print("Done Recv: {}".format(len(data)))
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    print("msg_size: {}".format(msg_size))
    while len(data) < msg_size:
        data += conn.recv(4096)

    print("hg state:" + str(current_hg_command))

    frame_data = data[:msg_size]
    data = data[msg_size:]
    data=pickle.loads(frame_data, fix_imports=True, encoding="bytes")

    ###############################################
    ### Do something with data from Atlas 200DK ###
    ###############################################

    # Tell Atlas that any movement command is complete
    if current_hg_command == "send_done_command":
         data = pickle.dumps("done command\n", 0)
         size = len(data)
         conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK
         current_hg_command = "none"

    # Execute and acknowledge reception of "Servo up" from Atlas
    elif data=="servo up\n":
            if current_hg_command == "none" or current_hg_command == "take_a_picture":
                move_up()
                print("Look up " + str(z_position))
            data = pickle.dumps("got it\n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Execute and acknowledge reception of "Servo down" from Atlas
    elif data=="servo down\n":
            if current_hg_command == "none" or current_hg_command == "take_a_picture":
                move_down()
                print("Look down " + str(z_position))
            data = pickle.dumps("got it\n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Execute and acknowledge reception of "Servo left" from Atlas
    elif data=="servo left\n":
            if current_hg_command == "none" or current_hg_command == "take_a_picture":
                move_left()
                print("Look left " + str(x_position))
            data = pickle.dumps("got it\n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Execute and acknowledge reception of "Servo right" from Atlas
    elif data=="servo right\n":
            if current_hg_command == "none" or current_hg_command == "take_a_picture":
                move_right()
                print("Look right " + str(x_position))
            data = pickle.dumps("got it\n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    #######################################################################################
    ### Sending information back to Atlas about which hand gesture command is executing ###
    #######################################################################################

    # Take a picture
    elif data=="take a picture\n":
            print("Take a picture")
            # display = "picture"
            if current_hg_command == "none":
                count_takeapicture = count_takeapicture + 1
                print("Takeapicture count:" + str(count_takeapicture))
                count_forward = 0
                count_backward = 0
                count_spin = 0
                if count_takeapicture == count_num:
                    print("Take a Picture triggered \n\n")
                    time_tap_start = 0
                    count_takeapicture = 0
                    current_hg_command = "take_a_picture"
                    data = pickle.dumps("received take a picture\n", 0)
                else:
                    data = pickle.dumps("got it \n", 0)
            else: 
                data = pickle.dumps("got it \n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 

   # Move Forwards
    elif data=="forward\n":
            print("Forward")
            if current_hg_command == "none":
                count_forward = count_forward + 1
                print("Forwards count: " + str(count_forward))
                count_takeapicture = 0
                count_backward = 0
                count_spin = 0
                if count_forward == count_num:
                   print("Forwards triggered \n\n")
                   count_forward = 0
                   current_hg_command = "forwards"
                   data = pickle.dumps("received forward\n", 0)
                else: 
                   data = pickle.dumps("got it \n", 0)
            else: 
                data = pickle.dumps("got it \n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 

    # Move Backwards
    elif data=="backward\n":
            print("Backward")
            if current_hg_command == "none":
                count_backward = count_backward + 1
                print("Backwards count: " + str(count_backward))
                count_takeapicture = 0
                count_forward = 0
                count_spin = 0
                if count_backward == count_num:
                    print("Backwards triggered \n\n")
                    count_backward = 0
                    current_hg_command = "backwards"
                    data = pickle.dumps("received backward\n", 0)
                else:
                    data = pickle.dumps("got it \n", 0)
            else: 
                data = pickle.dumps("got it \n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 

    # Spin Left
    elif data=="spin left\n":
            print("Spin left")
            if current_hg_command == "none":
                count_spin = count_spin + 1
                print("Spin count: " + str(count_spin))
                count_takeapicture = 0
                count_forward = 0
                count_backward = 0
                if count_spin == count_num:
                    print("Spin triggered \n\n")
                    count_spin = 0
                    current_hg_command = "spin_left"
                    data = pickle.dumps("received spin left\n", 0)
                else:
                    data = pickle.dumps("got it \n", 0)
            else: 
                data = pickle.dumps("got it \n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 

    # Spin Right
    elif data=="spin right\n":
            print("Spin right")
            if current_hg_command == "none":
                count_spin = count_spin + 1
                print("Spin count: " + str(count_spin))
                count_takeapicture = 0
                count_forward = 0
                count_backward = 0
                if count_spin == count_num:
                    print("Spin triggered \n\n")
                    count_spin = 0
                    current_hg_command = "spin_right"
                    data = pickle.dumps("received spin right\n", 0)
                else:
                    data = pickle.dumps("got it \n", 0)
            else: 
                data = pickle.dumps("got it \n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Left
    elif data=="left\n":
        print("Left")
        if current_hg_command == "none":
            count_takeapicture = 0
            count_forward = 0
            count_backward = 0
            print("Left triggered \n\n")
            current_hg_command = "left"
            data = pickle.dumps("received left\n", 0)
        else:
            data = pickle.dumps("got it \n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 
    
    # Right
    elif data=="right\n":
        print("Right")
        if current_hg_command == "none":
            count_takeapicture = 0
            count_forward = 0
            count_backward = 0
            print("Right triggered \n\n")
            current_hg_command = "right"
            data = pickle.dumps("received right\n", 0)
        else: 
            data = pickle.dumps("got it \n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Activate
    elif data=="activate\n":
        print("activate robot\n")
        display = "default"
        count_takeapicture = 0
        count_forward = 0
        count_backward = 0
        count_spin = 0
        data = pickle.dumps("received activate\n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 
    
    # Deactivate
    elif data=="deactivate\n":
        print("deactivate robot\n")
        display = "deactivate"
        count_takeapicture = 0
        count_forward = 0
        count_backward = 0
        count_spin = 0
        data = pickle.dumps("received deactivate\n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 

    # RESET
    elif data=="reset\n":
        print("reset robot\n")
        if display != "deactivate":
            display = "default"
        count_takeapicture = 0
        count_forward = 0
        count_backward = 0
        count_spin = 0
        data = pickle.dumps("received reset\n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 

    # Follow
    elif data=="follow\n":
        print("follow\n")
        display = "follow"
        count_takeapicture = 0
        count_forward = 0
        count_backward = 0
        count_spin = 0
        data = pickle.dumps("received follow\n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Stop follow
    elif data=="stop_follow\n":
        print("stop following\n")
        display = "default"
        count_takeapicture = 0
        count_forward = 0
        count_backward = 0
        count_spin = 0
        data = pickle.dumps("received stop_follow\n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Body detected
    elif data == "body\n":
        print("body\n")
        display = "body"
        data = pickle.dumps("received body\n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Centering for take a picture
    elif data=="center for picture\n":
        print("center for picture\n")
        display = "picture"
        data = pickle.dumps("received center\n", 0)
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK

    # Nothing to send, report "none" to Atlas anyways
    elif data=="none\n":
            # display = "default"
            if display == "body":
                display = "default"
            count_takeapicture = 0
            count_forward = 0
            count_backward = 0
            count_spin = 0
            data = pickle.dumps("got it\n", 0)
            size = len(data)
            conn.sendall(struct.pack(">L", size) + data) # Send data back to Atlas 200 DK 

    # Else, received photo from Atlas for Camera View feature of Take a Photo routine
    else:
        # print(data)
        frame = data
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        height_orig, width_orig, channels = frame.shape
        if time_tap_start == 0:
            time_tap_start = time.time()
        else:
            time_tap_start = time_tap_start
        if (width_orig>1 and height_orig>1): #Verify that image is valid
            frame_show = cv2.resize(frame, (width, height))
            
        # After 3 seconds of countdown, flash white on the screen and display the final taken picture for 5 seconds
        if current_hg_command == "take_a_picture" and (time.time() - time_tap_start) > 3: 
            data = pickle.dumps("done command\n", 0)
            current_hg_command = "tap_image_fade" # "Take a picture" image flashes white
            time_tap_image_fade = time.time()
            time_tap_start = 0
            fade_image = frame_show

        # Imprint countdown number on photo for Camera View (3...2...1...)
        else:
            cv2.putText(frame_show,str(int(math.ceil(3 - (time.time() - time_tap_start)))),(200,210),font, scale,color,thickness,cv2.LINE_AA)
            data = pickle.dumps("got it\n", 0)

        # Send data back to Atlas 200 DK 
        size = len(data)
        conn.sendall(struct.pack(">L", size) + data)

####################### vv State Machine for Current Hand Gesture Command vv ######################

    # Display Neutral expression by default
    if current_hg_command != "take_a_picture" and current_hg_command != "tap_image_fade" and current_hg_command != "tap_final_image_show":

        ret_val, frame_show = neu_cap.read()
        # Reset to beginning if neutral expression video has ended
        if not ret_val:
            neu_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_val, frame_show = neu_cap.read()
        frame_show = cv2.resize(frame_show, (width, height))

        # if current_hg_command == "forwards": #for debugging
        #     cv2.putText(frame_show,"F",(200,210),font, scale,color,thickness,cv2.LINE_AA)
        # if current_hg_command == "backwards": #for debugging
        #     cv2.putText(frame_show,"B",(200,210),font, scale,color,thickness,cv2.LINE_AA)
        # if current_hg_command == "spin": #for debugging
        #     cv2.putText(frame_show,"S",(200,210),font, scale,color,thickness,cv2.LINE_AA)

        if display == "deactivate":
            frame_show = cv2.resize(deactivate_img, (width, height))

        elif display == "picture":
            frame_show = cv2.resize(camera_img, (width, height))

        elif display == "follow":
            frame_show = cv2.resize(follow_img, (width, height))

        elif display == "body":
            frame_show = cv2.resize(body_img, (width, height))


#    ### Display happy mood after completion of any command. Return to neutral expression when complete
#     elif current_hg_command == "happy_mood":

#         ret_val, frame_show = happy_cap.read()
#         # Reset to beginning and start neutral expression if happy expression video has ended
#         if not ret_val:
#             happy_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#             neu_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#             current_hg_command = "none" # Go back to no hand gesture command being executed
#             ret_val,frame_show = neu_cap.read()
#         frame_show = cv2.resize(frame_show, (width, height))

   # Displays a white image to simulate the flash of a camera during "Take a Picture" routine
    elif current_hg_command == "tap_image_fade":
       frame_show = white_img
       if (time.time() - time_tap_image_fade) >= 1.5:
           current_hg_command = "tap_final_image_show"
           time_final_img_tap_start = time.time()
           frame_show = white_img
           if not os.path.exists("/home/pi/Desktop/saved_images/"):
               os.makedirs("/home/pi/Desktop/saved_images/")
           now = datetime.datetime.now()
           dt_string = now.strftime("%d-%m-%Y_%H:%M:%S")
           cv2.imwrite("/home/pi/Desktop/saved_images/image_" + str(dt_string) + ".jpg", fade_image) 

    # Show the saved image for a few seconds after "Take a Picture" routine
    elif current_hg_command == "tap_final_image_show":
        frame_show = fade_image # Saved image 
        
        if (time.time() - time_final_img_tap_start) >= 3:
            current_hg_command = "none" # Command is complete, execute happy expression
            display = "default"
            # Reset camera position
            go_to_angle(servo_x, START_X)
            go_to_angle(servo_z, START_Z)
            

    # Display GUI
    cv2.imshow('ImageWindow',frame_show)

    if cv2.waitKey(1) == ord('q'):
        break

neu_cap.release()
# happy_cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()