#This Python file is called by CrowJ_PiProject_FaceDetection.py, 
# and is meant to be in the same directory as that program.

import RPi.GPIO as GPIO
import time

#Method for firing the NERF blaster:
def shootNerfgun(angle, fire, angleUpValue, fireOnValue, fireOffValue, angleDownValue):

    time.sleep(0.25)
    angle.ChangeDutyCycle(angleUpValue)         # Move the NERF blaster to the firing position.
    time.sleep(0.5)
    angle.ChangeDutyCycle(0)  
    fire.ChangeDutyCycle(fireOnValue)           # Move the servo that pulls the trigger.
    time.sleep(0.2)
    fire.ChangeDutyCycle(fireOffValue)          # Reset position of the servo that pulls the trigger.
    time.sleep(0.2)
    fire.ChangeDutyCycle(0)
    angle.ChangeDutyCycle(angleDownValue)       # Reset the NERF blaster to the neutral position.
    time.sleep(0.5)
    angle.ChangeDutyCycle(0)
    time.sleep(1)
        
#Bigger number equals more ccw rotation.