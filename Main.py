import subprocess
import json

import serial
import serial.serialutil

from picamera2 import Picamera2
from sangaboard import Sangaboard
import time
import os

output_dir = "Images_Capture"
os.makedirs(output_dir, exist_ok=True)

picam2 = Picamera2()
config = picam2.create_still_configuration()
picam2.configure(config)
picam2.start()

print("ouverture du port en serie")
ser = serial
try:
    ser = ser.Serial("/dev/ttyACM0",9600,timeout=1)
    serial_port = "ouvert"
    print(f"port {ser} ouvert")
except serial.serialutil.SerialException as e:
    print(f"erreur probable le port est déjà utilisé: {e}")
    ser = None

if ser and ser.is_open:
    while ser.read():
        print("port en serie en cours d'envoie de données")

board = Sangaboard("/dev/ttyACM0")

start_x = 5000
end_x = 0
step_x = -500  

y_pos = 5000  

z_positions = [0, 200, 400] 
def run_hailo_inference(image_path):
    import hailo_platform 

    detections = hailo_infer(image_path)
    return detections


try:
    imageCount = 0

    board.move_abs([start_x, y_pos, 0])
    time.sleep(1)

    for x in range(start_x, end_x + step_x, step_x):
        board.move_abs([x, y_pos, 0])
        time.sleep(0.5)

        for z in z_positions:
            board.move_abs([x, y_pos, z])
            time.sleep(0.5)

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{output_dir}/image_{imageCount:02d}_X{x}_Z{z}_{timestamp}.jpg"

            picam2.capture_file(filename)
            print(f"Captured: {filename}")

            detections = run_hailo_inference(filename)
            print(f"Inference results for image {imageCount}: {detections}")

            imageCount += 1


finally:
    picam2.stop()
    board.release_motors()
    print(f"Capture complete. Images saved in: {output_dir}")  
    ser = None
    time.sleep(0.2)
    print("le port est fermé")
    board.close()


