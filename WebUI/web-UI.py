import time
import serial.serialutil
from flask import Flask, render_template_string, request, redirect,render_template
from sangaboard import Sangaboard
import os
import socket
import subprocess
import serial
import threading
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

app = Flask(__name__)

board = Sangaboard("/dev/ttyACM0")

motor_pos = {"X":0,
             "Y":0,
             "Z":0}
help_response = ""
movement_thread = None
movement_lock = threading.Lock()
stop_request = False
led_level = 0.0
PORT = 5000

@app.route("/")
def index():
    return render_template("WebUI.html",response=help_response,displayX=motor_pos["X"],displayY=motor_pos["Y"],displayZ=motor_pos["Z"])
    #return render_template_string(HTML,displayX=motor_pos["X"],displayY=motor_pos["Y"],displayZ=motor_pos["Z"])

def move_motors(x, y, z):
    global stop_request
    with movement_lock:
        if stop_request:
            return
        board.move_rel([x, y, z])
        motor_pos["X"] += x
        motor_pos["Y"] += y
        motor_pos["Z"] += z

@app.route("/move", methods=["POST"])
def move():
    global movement_thread, stop_request
    x = float(request.form.get("x", 0))
    y = float(request.form.get("y", 0))
    z = float(request.form.get("z", 0))
    stop_request = False
    movement_thread = threading.Thread(target=move_motors, args=(x, y, z))
    movement_thread.start()
    return redirect("/")

def move_motors_absolute(x, y, z):
    global stop_request
    with movement_lock:
        if stop_request:
            return
        board.move_abs([x, y, z])
        motor_pos["X"] = x
        motor_pos["Y"] = y
        motor_pos["Z"] = z

@app.route("/absolute", methods=["POST"])
def move_absolute():
    global movement_thread, stop_request
    x = float(request.form.get("x", 0))
    y = float(request.form.get("y", 0))
    z = float(request.form.get("z", 0))
    stop_request = False
    movement_thread = threading.Thread(target=move_motors_absolute, args=(x, y, z))
    movement_thread.start()
    return redirect("/")


@app.route("/zero_pos", methods=["POST"])
def set_zero():
    board.zero_position()
    return redirect("/")

@app.route("/stop", methods=["POST"])
def stop():
    global stop_request, movement_thread
    stop_request = True
    board.release_motors()
    print("Motors stopped.")
    return redirect("/")

@app.route("/help", methods=["POST"])
def help():
   global help_response
   help_response = board.print_help()
   return redirect("/")

@app.route("/setLed",methods=["POST"])
def set_led():
    "normalising value to get between 0 and 1"
    led_level = float(request.form.get("Light_level"))
    print(led_level)
    if led_level > 10 or led_level < 0:
        led_level = min(max(led_level / 10.0, 0), 1)
    
    board.set_light_level(led_level)
    return led_level
def kill_process_using_port(port):
    try:
        output = subprocess.check_output(["lsof", "-i", f":{port}"]).decode()
        for line in output.splitlines()[1:]:
            parts = line.split()
            pid = int(parts[1])
            os.kill(pid, 9)
            print(f"libere le process {pid} sur le port {port}")
            app.run(host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"erreur: {e}")

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    except:
        kill_process_using_port(PORT)
        app.run(host="0.0.0.0", port=5000)
    finally:
        ser = None
        time.sleep(0.2)
        print("le port est fermé")
        board.close()
