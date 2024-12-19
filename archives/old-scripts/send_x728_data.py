import smbus2
import requests
import json

# I2C bus and X728 address (commonly 0x36 for the X728 UPS)
bus = smbus2.SMBus(1)
i2c_address = 0x36

# Function to read battery voltage
def read_voltage():
    voltage_raw = bus.read_word_data(i2c_address, 0x02)  # Register for voltage
    voltage = voltage_raw * 78.125 / 1000000  # Conversion factor for voltage
    return voltage

# Function to read battery capacity
def read_capacity():
    capacity_raw = bus.read_word_data(i2c_address, 0x04)  # Register for capacity
    return capacity_raw

# Function to check power status
def read_power_status():
    status_raw = bus.read_byte_data(i2c_address, 0x01)  # Register for power status
    if status_raw == 0:
        return "Battery"
    else:
        return "External Power"

# Read the values
voltage = read_voltage()
capacity = read_capacity()
power_status = read_power_status()

# SignalK server URL
signalk_url = "http://192.168.1.100:3000/signalk/v1/api/"

# Prepare data in SignalK format
data = {
    "updates": [
        {
            "values": [
                {"path": "electrical.batteries.0.voltage", "value": voltage},
                {"path": "electrical.batteries.0.capacity", "value": capacity},
                {"path": "notifications.batteries.0.powerStatus", "value": power_status}
            ]
        }
    ]
}

# Send data to SignalK using REST API
response = requests.post(signalk_url, json=data)

# Check response status
if response.status_code == 200:
    print("Data sent successfully!")
else:
    print(f"Failed to send data. Status code: {response.status_code}")
