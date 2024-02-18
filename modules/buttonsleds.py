import smbus
import time
import subprocess
import requests
import json
from socketIO_client import SocketIO

MCP23017_IODIRA = 0x00  # I/O direction register for Port A
MCP23017_IODIRB = 0x01  # I/O direction register for Port B
MCP23017_GPIOA = 0x12   # Register for outputs on Port A
MCP23017_GPIOB = 0x13   # Register for outputs on Port B
MCP23017_GPPUA = 0x0C   # Pull-up resistors configuration for Port A
MCP23017_GPPUB = 0x0D   # Pull-up resistors configuration for Port B
MCP23017_ADDRESS = 0x27

print("Configuring MCP23017 I/O expander.")

# Initialize SMBus
bus = smbus.SMBus(1)

print("SMBus initialized.")

# Port B: Set PB0 and PB1 as output, PB2-PB5 as input with pull-up resistors
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRB, 0x3C)  # 0b00111100 - PB0-PB1 as output, PB2-PB5 as input
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPPUB, 0x3C)   # Enable pull-ups for PB2-PB5

# Port A: Set as outputs for LEDs
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRA, 0x00)  # Outputs: PA0-PA7

print("MCP23017 ports configured.")

print("Starting the Volumio button interface script.")

VOLUMIO_URL = "http://localhost:3000/api/v1/commands/?cmd="

volumioIO = SocketIO('localhost', 3000)

print("Connected to Volumio over SocketIO.")

prev_button_state = [0 for _ in range(8)]

# 4 rows, 2 columns with swapped column numbers
button_map = [
    [2, 1],  # Row 1
    [4, 3],  # Row 2
    [6, 5],  # Row 3
    [8, 7]   # Row 4
]


def read_button_matrix():
    button_matrix_state = [0 for _ in range(8)]
    for column in range(2):
        # Drive one column low at a time (for PB0 and PB1)
        bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOB, ~(1 << column) & 0x03)
        # Read the state of the row pins (PB2-PB5)
        row_state = bus.read_byte_data(MCP23017_ADDRESS, MCP23017_GPIOB) & 0x3C
        # Update the button matrix state
        for row in range(4):
            # Shift row_state right by 2 to align with PB2 starting position
            button_matrix_state[(column + 1) * row] = (row_state >> (row + 2)) & 1
    return button_matrix_state


def control_leds(led_state):
    # print(f"Setting LED state to {led_state}.")
    bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOA, led_state)


# Volumio Activation Functions (These are your provided functions)


def activate_play():
    print("Activating play.")
    try:
        volumioIO.emit('play')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Playback started.")


def activate_pause():
    print("Activating pause.")
    try:
        volumioIO.emit('pause')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Playback paused.")


def activate_back():
    print("Activating previous track.")
    try:
        volumioIO.emit('previous')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Track skipped back.")


def activate_forward():
    print("Activating next track.")
    try:
        volumioIO.emit('next')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Track skipped forward.")


def activate_shuffle():
    try:
        volumio_state = get_volumio_state()
        if volumio_state and "random" in volumio_state:
            current_random = volumio_state["random"]
            new_random_mode = not current_random
            volumioIO.emit('setRandom', {'value': new_random_mode})
    except Exception as e:
        print("Error: ", e)
    else:
        print("Random mode toggled.")


def activate_repeat():
    try:
        volumio_state = get_volumio_state()
        if volumio_state and "repeat" in volumio_state:
            current_repeat = volumio_state["repeat"]
            new_repeat_mode = not current_repeat
            volumioIO.emit('setRepeat', {'value': new_repeat_mode})
    except Exception as e:
        print('Error:', e)
    else:
        print('Repeat mode toggled.')


def activate_favourites():
    try:
        volumioIO.emit('playPlaylist', {'name': 'favourites'})
    except Exception as e:
        print("Error: ", e)
    else:
        print("Favourites playlist loaded.")


def activate_ButtonC():
    print("ButtonC pressed.")
    print("ButtonC action performed")


def get_volumio_state():
    # print("Fetching Volumio state.")
    try:
        response = requests.get("http://localhost:3000/api/v1/getState")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        return None
    else:
        return json.loads(response.text)


print("Starting button check loop.")

VOLUMIO_STATE_TO_LED = {
    'play': 0b00000001,  # Example LED pattern for play state
    'stop': 0b00000010,  # Example LED pattern for pause state
}


def update_leds_with_volumio_state():
    volumio_state = get_volumio_state()
    if volumio_state:
        status = volumio_state.get('status')
        led_pattern = VOLUMIO_STATE_TO_LED.get(status, 0)  # Default to 0 (all LEDs off) if status not found
        control_leds(led_pattern)


def check_buttons_and_update_leds(button_c_callback=None):
    global prev_button_state  # Use the global variable prev_button_state
    buttons = read_button_matrix()

    # Define the button actions here, as an example
    button_action_map = {
        0: activate_play,
        1: activate_pause,
        2: activate_back,
        3: activate_forward,
        4: activate_shuffle,
        5: activate_repeat,
        6: activate_favourites,
        7: activate_ButtonC,
    }

    # Check if a button is pressed
    for button_id in range(8):
        current_button_state = buttons[button_id]
        if current_button_state == 0 and prev_button_state[button_id] != current_button_state:
            print(f"Button {button_id} pressed")

            # Call the injected ButtonC_PushEvent function passed as a parameter
            if button_id == 7 and button_c_callback is not None:
                button_c_callback()

            # Call the function associated with the button_id from the map
            if button_id in button_action_map:
                button_action_map[button_id]()

            # Update the previous button state
            prev_button_state[button_id]

    # Wait a bit before checking again to debounce
    time.sleep(0.1)
