import time
import json
from websocket import create_connection
from smbus2 import SMBus

# I2C address and bus
I2C_ADDRESS = 0x36
bus = SMBus(1)  # For Raspberry Pi models with I2C bus 1

# Signal K server WebSocket URL (adjust if necessary)
signalk_url = 'ws://localhost:3000/signalk/v1/stream'

def read_voltage():
    # Read voltage from x728 via I2C
    read = bus.read_word_data(I2C_ADDRESS, 2)
    # Swap bytes because data is in little-endian format
    voltage_raw = ((read & 0xFF) << 8) | (read >> 8)
    voltage = voltage_raw * 78.125 / 1_000_000  # Convert to volts
    return voltage

def read_capacity():
    # Read capacity percentage from x728 via I2C
    read = bus.read_word_data(I2C_ADDRESS, 4)
    capacity_raw = ((read & 0xFF) << 8) | (read >> 8)
    capacity = capacity_raw / 256  # Convert to percentage
    return capacity
def send_to_signalk(ws, voltage, capacity):
    delta = {
  "context": "vessels.self",
  "updates": [
    {
      "source": {
        "label": "x728",
        "type": "BatteryMonitor"
      },
#      "timestamp": "2024-09-29T17:00:00Z",
      "values": [
        {
          "path": "electrical.batteries.x728.voltage",
          "value": 12.34
        },
        {
          "path": "electrical.batteries.x728.capacity.stateOfCharge",
          "value": 0.95
        }
      ]
    }
  ]
}

    # Print delta message for debugging
    print("Delta message being sent:")
    print(json.dumps(delta, indent=2))
    # Send delta message to Signal K server
    ws.send(json.dumps(delta))


def main():
    # Establish WebSocket connection once
    ws = create_connection(signalk_url)
    try:
        while True:
            voltage = read_voltage()
            capacity = read_capacity()
            send_to_signalk(ws, voltage, capacity)
            time.sleep(60)  # Wait for 60 seconds before next reading
    except KeyboardInterrupt:
        print("Script interrupted by user.")
    finally:
        ws.close()

if __name__ == '__main__':
    main()
