#This Python file is called by CrowJ_PiProject_FaceDetection.py, 
# and is meant to be in the same directory as that program.

import RPi.GPIO as GPIO
import time

def init():   					# Initialzed the GPIO pins (unused because it conflucted with thread_tracking in CrowJ_PiProject_FaceDetection.py).
	#GPIO.setmode(GPIO.BCM)
	GPIO.setup(17, GPIO.OUT)
	GPIO.setup(22, GPIO.OUT)
	GPIO.setup(23, GPIO.OUT)
	GPIO.setup(24, GPIO.OUT)

def forward(sec):				# Method to make the chassis move forward (unused).
	#init()
	GPIO.output(17, False)
	GPIO.output(22, True)
	GPIO.output(23, True)
	GPIO.output(24, False)
	time.sleep(sec)
	#GPIO.cleanup() 
	
def reverse(sec):				# Method to make the chassis move backwards (unused).
	#init()
	GPIO.output(17, True)
	GPIO.output(22, False)
	GPIO.output(23, False)
	GPIO.output(24, True)
	time.sleep(sec)
	#GPIO.cleanup()
	
def left_turn(sec):				# Method to make the chassis move left for set amount of seconds (is used).
	#init() 
	GPIO.output(17, True)
	GPIO.output(22, False)
	GPIO.output(23, True)
	GPIO.output(24, False)
	time.sleep(sec)
	#GPIO.cleanup()
	
def right_turn(sec):			# Method to make the chassis move right for set amount of seconds (is used).
	#init()
	GPIO.output(17, False)
	GPIO.output(22, True)
	GPIO.output(23, False)
	GPIO.output(24, True)
	time.sleep(sec)
	#GPIO.cleanup()

def halt():						# Method to make the chassis stop moving (is used).
	GPIO.output(17, False)
	GPIO.output(22, False)
	GPIO.output(23, False)
	GPIO.output(24, False)
	#GPIO.cleanup()