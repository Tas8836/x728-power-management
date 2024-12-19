import gpiod
import time
import struct
import smbus
import subprocess
import logging
import requests
import os
import socket

# Setup logging
log_dir = os.path.expanduser('~/logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'x728_power_management.log')

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
)

# Signal K Server Configuration
SIGNAL_K_URL = "http://192.168.0.100:3000/signalk/v1/api/vessels/self"

# Unique Source Label
SOURCE_LABEL = "x728ups_battery_monitor"

# GPIO and I2C Setup
chipname = "gpiochip0"
line_offset = 6
out_line_offset = 26
I2C_ADDR = 0x36

# I2C bus setup
bus = smbus.SMBus(1)

# Open the GPIO chip
chip = gpiod.Chip(chipname)

# Get the input line for power loss detection
line = chip.get_line(line_offset)
line.request(consumer="x728_power_management", type=gpiod.LINE_REQ_EV_BOTH_EDGES)

# Get the output line to trigger safe shutdown
out_line = chip.get_line(out_line_offset)
out_line.request(consumer="x728_power_management", type=gpiod.LINE_REQ_DIR_OUT)

# Set the delay time in seconds before shutting down after power loss
SHUTDOWN_DELAY = 30  # Adjust the delay as needed

def send_to_signal_k(path, value):
    payload = {
        "context": "vessels.self",
        "updates": [
            {
                "source": {
                    "label": SOURCE_LABEL
                },
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "values": [
                    {
                        "path": path,
                        "value": value
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    logging.info(f"Sending to Signal K: {payload}")

    try:
        response = requests.patch(SIGNAL_K_URL, json=payload, headers=headers)
        response.raise_for_status()
        logging.info(f"Sent {path}: {value} to Signal K successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending data to Signal K: {e}")
        logging.debug(f"Payload: {payload}")


def read_voltage(bus):
    read = bus.read_word_data(I2C_ADDR, 2)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    voltage = swapped * 1.25 / 1000 / 16
    voltage = round(voltage, 2)
    send_to_signal_k("electrical.batteries.x728ups_battery.voltage", voltage)
    return voltage

def read_capacity(bus):
    read = bus.read_word_data(I2C_ADDR, 4)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    capacity = swapped / 256
    capacity = min(100, capacity)
    capacity = round(capacity, 2)
    send_to_signal_k("electrical.batteries.x728ups_battery.capacity.stateOfCharge", capacity)
    return capacity

def shutdown_sequence():
    logging.info(f"Delaying shutdown for {SHUTDOWN_DELAY} seconds.")
    time.sleep(SHUTDOWN_DELAY)
    logging.info("Running safe shutdown with xSoft.sh.")
    subprocess.call(['sudo', '/usr/local/bin/xSoft.sh', '0', '26'])
    logging.info("Pi shutdown sequence initiated.")
    time.sleep(2)
    out_line.set_value(1)
    time.sleep(3)
    out_line.set_value(0)
    logging.info("UPS shutdown signal sent.")
    send_to_signal_k("notifications.shutdown", {
        "state": "alert",
        "method": ["visual", "sound"],
        "message": "Shutdown initiated due to low battery"
    })

def handle_event(event):
    if event.event_type == gpiod.LineEvent.RISING_EDGE:
        logging.info("---AC Power Loss OR Power Adapter Failure---")
        logging.info(f"Shutdown in {SHUTDOWN_DELAY} seconds.")
        send_to_signal_k("notifications.power", {
            "state": "alert",
            "method": ["visual", "sound"],
            "message": "AC Power Loss or Adapter Failure"
        })
        shutdown_sequence()
    elif event.event_type == gpiod.LineEvent.FALLING_EDGE:
        logging.info("---AC Power OK, Power Adapter OK---")
        send_to_signal_k("notifications.power", {
            "state": "normal",
            "message": "AC Power OK, Power Adapter OK"
        })

try:
    # Main loop to monitor events and battery status
    while True:
        # Monitor power loss events
        event = line.event_wait(sec=0)
        if event:
            event = line.event_read()
            handle_event(event)

        # Monitor battery status
        voltage = read_voltage(bus)
        capacity = read_capacity(bus)
        logging.info(f"Voltage: {voltage:.2f}V, Capacity: {capacity:.0f}%")

        # Shutdown if battery is critically low
        if capacity < 35 or voltage < 3.0:
            logging.info("Battery is critically low. Initiating shutdown...")
            send_to_signal_k("notifications.battery", {
                "state": "alert",
                "method": ["visual", "sound"],
                "message": "Battery is critically low. Shutting down."
            })
            shutdown_sequence()
            break

        time.sleep(2)
except KeyboardInterrupt:
    logging.info("Exiting...")
finally:
    chip.close()
