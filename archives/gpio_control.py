import gpiod
import sys

def control_gpio(pin, state):
    # Open the GPIO chip (e.g., gpiochip0)
    chip = gpiod.Chip('gpiochip0')
    
    # Get access to the line (pin number) specified
    line = chip.get_line(pin)
    
    # Request the line as an output
    line.request(consumer="signalk-plugin", type=gpiod.LINE_REQ_DIR_OUT)
    
    # Set the line to the specified value (0 for low, 1 for high)
    line.set_value(state)

if __name__ == "__main__":
    # The script expects 2 arguments: pin number and state (0 or 1)
    pin = int(sys.argv[1])  # Pin number from the command line
    state = int(sys.argv[2])  # State (0 or 1) from the command line
    control_gpio(pin, state)
