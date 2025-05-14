# PROGRAM:              CrowJ_PiProject_FaceDetection.py
# Version: 2			The code was cleaned up after the presentation (Added a boolean to control debug print statemetns, removed unused code, and added some more comments).
#
# COURSE:               COSC3143-01 Pi & Python
# AUTHOR:               Jared Crow, Matthew Killy, Sam Kundt (Team South Hall)
# ASSIGNMENT:           Project Submission
# PURPOSE:              With a camera and chassis, allow the Pi to shoot a NERF dart at somebody if it detects a face.
# DEPENDENCIES:         SamK_PiProject_Chassis.py, MatthewK_PiProject_NerfShoot.py,
#                       OpenCV, numpy, time, Picamera 2, threading

# OPERATIONAL STATUS: 	Program works as from on top of a desk. Need to make it accurate at shooting from the ground.
# Features to add:      1) Make sure the robot is as accurate as it can be.
#						2) Might need to slow down the movement of the chassis when in the patrolling state.
#                       3) Account for the case when a face is very close.
#                       4) If time, add a feature that makes it so if the chassis was last moving one direction while tracking,
#                       it will move the opposite direction when it switches back to patrolling.
#                       5) Polish up the code. Remove redundant parts.

#References:            Face tracking code by automaticdai on GitHub.
#                       https://github.com/automaticdai/rpi-object-detection?tab=readme-ov-file#31-camera-test

# Other Note(s)         - Any variables created by Jared Crow for this project have the follwing naming convention: variableType_variableName.
#						- DON'T USE CTRL-C TO EXIT THE PROGRAM. Use the ESC key isntead.

#!/usr/bin/python3

#OpenCV imports:
import cv2
import numpy as np
import time
from picamera2 import Picamera2

#Threading imports:
import threading
import time

#GPIO imports:
import RPi.GPIO as GPIO

#Imports from 2 other py programs:
import SamK_PiProject_Chassis
import MatthewK_PiProject_NerfShoot

#DEBUG MODE:
b_debugMode = False									#Set this variable to TRUE to make the program print to the command line while running.

#Variables for Face tracking:                       # This program has 2 states: PATROLLING and TRACKING
int_state = 0                                       # Equals 0 if system should be PATROLLING. Equals 1 if system is TRACKING a face. Used as a global variable. 
face_largestFace = (0,0,0,0)                        # In the event of multiuple detected faces, this is used to pick the largest face, which is the face that is tracked in the TRACKING state.
f_initialTime = time.time()                         # The initial time that the program starts. Used to have the system wait 3 seconds after starting before it tries tracking faces.
b_firstPatrol = True                                # When True, causes the system to wait 2 seconds before it starts PATROLLING. Becomes False when the system starts PATROLLING for the first time.

#GPIO setup:
GPIO.setmode(GPIO.BCM)                              # Sets the GPIO mode to BCM.
#GPIO setup for the chassis (by Sam):
GPIO.setup(17, GPIO.OUT)                            # Pins 17 and 23 are for the left tread on the chassis.
GPIO.setup(22, GPIO.OUT)                            # Pins 22 and 24 are for the right tread on the chassis.
GPIO.setup(23, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)
#Setup for firing the blaster (by Matthew):
firePIN = 25                                        # The pin for pulling the trigger of the NERF blaster.
anglePIN = 27                                       # The pin for rotating the NERF blaster up or down.
GPIO.setup(firePIN, GPIO.OUT)
GPIO.setup(anglePIN, GPIO.OUT)

fireOnValue = 8                                     # Position the 1st servo moves to when NERF blaster isnt being shot.
fireOffValue = 8.8                                  # Position the 1st servo moves to to pull the trigger.
angleUpValue = 5.875 #5.8                                  # Position the 2nd servo moves to to aim up.
angleDownValue = 5.6 #7.3                             # Position the 2nd servo moves to when the NERF gun is at rest. 

f_turnAmount = .07#05 #.10						# The amount the chassis moves by every f_timeStop seconds.
f_timeStop = .5 #.20
str_direction = 'right'						# A string to signify what direction the chassis should turn.

#Initialization for the 1st servo (the servo that pulls the trigger):
fire = GPIO.PWM(firePIN, 50)                        # GPIO 17 for PWM with 50Hz
fire.start(fireOffValue)
time.sleep(0.1)
fire.ChangeDutyCycle(0)

# Initialization for the 2nd servo (the servo that rotates the blaster up or down):
angle = GPIO.PWM(anglePIN, 50)                      # GPIO 27 for PWM with 50Hz
angle.start(angleDownValue)
time.sleep(0.1)
angle.ChangeDutyCycle(0)

#Methods:
def visualize_fps(image, fps: int):					# Method from the borrowed Face Deteciton code. It displays the FPS of what the camera sees.
	if len(np.shape(image)) < 3:
		text_color = (255, 255, 255)  # white
	else:
		text_color = (0, 255, 0)  # green
	row_size = 20  # pixels
	left_margin = 24  # pixels

	font_size = 1
	font_thickness = 1

	# Draw the FPS counter
	fps_text = 'FPS = {:.1f}'.format(fps)
	text_location = (left_margin, row_size)
	cv2.putText(image, fps_text, text_location, cv2.FONT_HERSHEY_PLAIN,
				font_size, text_color, font_thickness)

	return image

def thread_patroling(name):							# Method for the PATROLLING thread:
	global b_debugMode
	if(b_debugMode):									# If debug mode enabled, print to let the user know thread_patrolling has started.
		print("thread_patroling started")
	time.sleep(.5)										# Wait .5 seconds before starting the PATROLLING state.
	global b_firstPatrol
	if(b_firstPatrol):									# Wait an additional 2 seconds ebfore starting if the program is booting up for the first time.
		time.sleep(2)
		b_firstPatrol = False
	
	while True:
		global int_state                            	# Constantly get the value of int_state every loop.
		global f_turnAmount
		global f_timeStop
		global str_direction
		b_previouslyTracking = False					# Boolean that equals true if the last thing the system was doing was tracking.
		
		if int_state == 0:								# If in the PATROLLING state, system should be patrolling.
			for i in range(0, 100):						# First, move right (or left) by 100 steps.
				if int_state == 1:							# If state changes while patrolling, stop patrolling.
					SamK_PiProject_Chassis.halt()
					break
				if(str_direction == 'right'):			# If statements to determine whether chassis should move right or left.
					if(b_debugMode):									# If debug mode enabled, print to let user know chassis should be turning right.
						print("Patroling right")
					SamK_PiProject_Chassis.right_turn(f_turnAmount)		# Calls a method from Sam's py file to turn the chassis right.
				elif(str_direction == 'left'):
					if(b_debugMode):
						print("Patroling left")							# If debug mode enabled, print to let user know chassis should be turning right.
					SamK_PiProject_Chassis.left_turn(f_turnAmount)		# Calls a method from Sam's py file to turn the chassis left.
				SamK_PiProject_Chassis.halt()
				time.sleep(f_timeStop)
			time.sleep(.5)
			SamK_PiProject_Chassis.halt()
			if(b_previouslyTracking):
				if(str_direction == 'right'):				#Change the current direction of patrolling once one direciton has gone for long enough.
					str_direction = 'left'
				elif(str_direction == 'left'):
					str_direction = 'right'
				b_previouslyTracking = False
		else:
			b_previouslyTracking = True


def thread_tracking(name):							# The method for the TRACKING thread.
	global b_debugMode
	if(b_debugMode):								# If debug mode enabled, print to let user know thread_tracking started.
		print("thread_tracking started")					
	global int_state                                	# Only need to get value of int_state once.
	global str_direction
	face_prevFace = (0,0,0,0)							# Used to determine if the detected face isn't moving for too long.
	f_startTime = time.time()							# Used to determine how long the face goes without moving. If the face stays perfectly still, its no longer in range.
	f_startTime2 = time.time()							# Used to determine if the system goes too long without firing at its target.
	f_timeMove = 0.015 / 2								# How much the chassis moves by every f_timeWait seconds.
	f_timeWait = 0.05

	global angle										# Globals for firing the NERF blaster when face is in range.
	global fire
	global angleUpValue
	global fireOnValue
	global fireOffValue
	global angleDownValue

	int_rangeOffset = 30        							# If greater than 0, offsetts the fire range to account for IRL imperfections of the robot.
	#Coordinates for the fire range: Used to determine if the tracked face is in the center of the system's view.
	int_fireRangeW = 125
	int_fireRangeH = 480
	int_fireRangeX = (640 // 2) - int_rangeOffset - (int_fireRangeW // 2)
	int_fireRangeY = (480 // 2) - (int_fireRangeH // 2)
	
	#While both of the timers haven't expired:
	while ((time.time() - f_startTime) <= 1.0 and (time.time() - f_startTime2) < 3):
		global face_largestFace							# Update the face being tracked every loop iteraiton.
		
		#Draws a rectangle every iteration to represent the fire range (colored yellow):
		cv2.rectangle(img, (int_fireRangeX, int_fireRangeY), (int_fireRangeX+int_fireRangeW, int_fireRangeY+int_fireRangeH), (0, 255, 255), 2)
		#Draws a rectangle every iteration to represent the face being tracked (colored red):
		cv2.rectangle(img, (face_largestFace[0], face_largestFace[1]), (face_largestFace[0]+face_largestFace[2], face_largestFace[1]+face_largestFace[3]), (0, 0, 255), 2)

		#If the face being tracked is in the center of the camera's view (fire range), fire the blaster:
		if(face_largestFace[0] >= int_fireRangeX and face_largestFace[0] + face_largestFace[2] <= int_fireRangeX + int_fireRangeW):
			SamK_PiProject_Chassis.halt()
			if(b_debugMode):							# If debug mode enabled, print to let user know NERF dart is about to be fired.
				print("About to fire")
			#Calls a method from Matthew's py file to shoot the NERF dart:
			MatthewK_PiProject_NerfShoot.shootNerfgun(angle, fire, angleUpValue, fireOnValue, fireOffValue, angleDownValue)
			break
		else:
			#If the detected face is to the left of the range, move the chassis left.
			if(face_largestFace[0] < int_fireRangeX):# or face_largestFace[0] + face_largestFace[2] >= int_fireRangeX):
				SamK_PiProject_Chassis.left_turn(f_timeMove)
				SamK_PiProject_Chassis.halt()
				if(b_debugMode):						# If debug mode enabled, print to let user know the system is moving left while targeting a face.
					print("Tracking left")
				str_direction = 'left'

				f_startTime -= f_timeMove
			#If the detected face is to the right of the range, move the chassis right.
			if(face_largestFace[0] + face_largestFace[2] > int_fireRangeX + int_fireRangeW):# or face_largestFace[0] <= int_fireRangeX + int_fireRangeW):
				SamK_PiProject_Chassis.right_turn(f_timeMove)
				SamK_PiProject_Chassis.halt()
				if(b_debugMode):						# If debug mode enabled, print to let user know the system is moving left while targeting a face.
					print("Tracking right")
				str_direction = 'right'

				f_startTime -= f_timeMove

			#The following if statement accounts for IRL imperfections of the system.
			# For some reason, the chassis treads get faster the more they are used, 
			# so this increases the time between each movmement to prevent this quirk 
			# from compromising the system's accuracy.
			# This is also why f_startTime2 exists. If the TRACKING state becomes too slow, the TRACKIGN state ends and immediatley starts again to reset the speed of the treads.
			if(f_timeWait < 0.25):
				f_timeWait += 0.009
			
		#If the tracked face isn't compeltely, perfectly still:
		if(face_largestFace != face_prevFace):
			f_startTime = time.time()
		else:
			#Let f_startTime run if the detection stays perfectly still (meaning the tracked face has been lost):
			if(b_debugMode):
				print("Time until state ends = " + str((time.time() - f_startTime)))	# If debug mode enabled, print to let user know how much time left before tracking state ends and tries again.
			
		face_prevFace = face_largestFace				# Update face_prevFace
		time.sleep(f_timeWait)							# Wait f_timeWait seconds before moving the chassis again.
		
	#If debug mode enabled, print statements to help report how the TRACKING state ends:
	if(b_debugMode):
		if ((time.time() - f_startTime) >= 3):				
			print("thread_tracking ending - timeout")
		else:
			print("thread_tracking ending - shot fired")
	int_state = 0										# Right as the TRACKING state ends, change the state back to PATROLLING.



# Load the cascade (from the borrowed Face Deteciton code):
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
l_faces = []

# Initialize Picamera2 and configure the camera (from the borrowed Face Deteciton code):
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()
fps = 0
b_notTracking = True
b_faceDetected = False

#Start the PATROLLING thread:
th_patroling = threading.Thread(target=thread_patroling, args=(1,), daemon=True)
th_patroling.start()
#Coordinates for the main range for detecting faces. Don't want the system to detect something too low.
int_rangeW = 550
int_rangeH = 390
int_rangeX = (640 // 2) - (int_rangeW // 2)
int_rangeY = (480 // 2) - 45 - (int_rangeH // 2)


#Main loop for detecting faces from the camera every iteraion:
while True:
	#(from the borrowed Face Deteciton code):
	# ----------------------------------------------------------------------
	# record start time
	start_time = time.time()						# I just realized f_initialTime is redundant because start_time exists, but leaving it like this doesn't harm anything.
	# Read the frame
	img = picam2.capture_array()
	# Convert to grayscale
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	# Detect the faces
	l_faces = face_cascade.detectMultiScale(gray, 1.1, 4)
	
	#Draw a green rectangle to represent the main range:
	cv2.rectangle(img, (int_rangeX, int_rangeY), (int_rangeX+int_rangeW, int_rangeY+int_rangeH), (0, 255, 0), 2)

	if(int_state == 0):								# If state is PATROLLING, b_notTracking is true.
		b_notTracking = True

	l_targets = []									# The list of all currently detected faces.

	#Draw a blue rectangle around every detected face:
	for (x, y, w, h) in l_faces:
		cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)

		#If face detected in acceptable range, add that face to the list of targets.
		if(x > int_rangeX and x+w < int_rangeX + int_rangeW and y > int_rangeY and y+h < int_rangeY + int_rangeH and h >= 40):	# Making sure the face is centered.
			l_targets.append((x, y, w, h))
     
	#Find the largest face from the list of detected faces (to shoot):
	if(len(l_targets) > 0 and time.time() - f_initialTime > 3):
		face_largestFace = max(l_targets)
		int_largestFaceIndex = l_targets.index(face_largestFace)
		
		# If the program isn't already tracking, change the state to TRACKING and start the TRACKING thread:
		if(b_notTracking):
			int_state = 1       
			th_tracking = threading.Thread(target=thread_tracking, args=(1,), daemon=True)
			th_tracking.start()

			b_notTracking = False

	#Displaying what the camera sees (from the borrowed Face Deteciton code):
	cv2.imshow('img', visualize_fps(img, fps))                      # This diplays the window.
	# ----------------------------------------------------------------------
	# record end time
	end_time = time.time()
	# calculate FPS
	seconds = end_time - start_time
	fps = 1.0 / seconds
	#print("Estimated fps:{0:0.1f}".format(fps))					# Print statement from the borrowed face detection code that isn't needed.
	# Stop if escape key is pressed:
	k = cv2.waitKey(30) & 0xff
	if k==27:
		break
		

#Release the VideoCapture object, and do cleanup at the end of the program:
picam2.close()
GPIO.output(17, False)
GPIO.output(22, False)
GPIO.output(23, False)
GPIO.output(24, False)
angle.ChangeDutyCycle(angleDownValue)
GPIO.cleanup()
print("GPIO cleaned up")											# Let user knwo that GPIO cleaned up at the end of the program.
cv2.destroyAllWindows()
