# Import required libraries
from nr1ui import ButtonC_PushEvent
import smbus
import time
import requests
from modules.pushbutton import PushButton
from modules.rotaryencoder import RotaryEncoder


# MCP23017 register definitions
MCP23017_IODIRA = 0x00  # I/O direction register for Port A
MCP23017_IODIRB = 0x01  # I/O direction register for Port B
MCP23017_GPIOA = 0x12   # Register for outputs on Port A
MCP23017_GPIOB = 0x13   # Register for outputs on Port B
MCP23017_GPPUA = 0x0C   # Pull-up resistors configuration for Port A
MCP23017_GPPUB = 0x0D   # Pull-up resistors configuration for Port B
MCP23017_ADDRESS = 0x27

# Initial configuration
print("Configuring MCP23017 I/O expander.")
bus = smbus.SMBus(1)  # Initialize SMBus
print("SMBus initialized.")

# Configure Port B: PB0 and PB1 as output, PB2-PB5 as input with pull-up resistors
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRB, 0x3C)
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPPUB, 0x3C)

# Configure Port A as outputs for LEDs
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRA, 0x00)
print("MCP23017 ports configured.")

prev_buttons = [0 for _ in range(8)]

ROTARY_ENCODER_LEFT = 13
ROTARY_ENCODER_RIGHT = 5
ROTARY_ENCODER_PUSH_BUTTON = 6


def check_rotary_encoder(direction):
    if direction == RotaryEncoder.LEFT:
        print(f"Rotary Ecoder: Left")
    if direction == RotaryEncoder.RIGHT:
        print(f"Rotary Ecoder: Right")


print("Configuring Rotary Encoder")
rotary_encoder = RotaryEncoder(ROTARY_ENCODER_LEFT, ROTARY_ENCODER_RIGHT, pulses_per_cycle=4)
rotary_encoder.setCallback(check_rotary_encoder)


def check_rotary_button(hold_time: float) -> None:
    print(f"Rotary Encoder Button Pressed: hold_time = {hold_time}")


print("Configuring Rotary Encoder PushButton")
rotary_push_button = PushButton(ROTARY_ENCODER_PUSH_BUTTON, max_time=2)
rotary_push_button.setCallback(check_rotary_button)


def read_button_matrix():
    button_matrix_state = [0 for _ in range(8)]
    for column in range(2):
        bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOB, ~(1 << column) & 0x03)
        time.sleep(0.005)
        row_state = bus.read_byte_data(MCP23017_ADDRESS, MCP23017_GPIOB) & 0x3C
        for row in range(4):
            state = (row_state >> (row + 2)) & 1
            index = row * 2 + 1 - column
            # print(f"index {index} state {state}")
            button_matrix_state[index] = state
    return button_matrix_state


def control_leds(led_state):
    print(f"Setting LED state to {led_state}.")
    bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOA, led_state)


def check_buttons_and_update_leds() -> None:
    global prev_buttons

    buttons = read_button_matrix()
    # print(f"buttons {buttons}")
    for button_id in range(8):
        current_button_state = buttons[button_id]
        if current_button_state == 0 and prev_buttons[button_id] != current_button_state:
            print(f"Button {button_id} pressed")
            led_state = 1 << (button_id)
            control_leds(led_state)
        prev_buttons[button_id] = current_button_state
        time.sleep(0.05)


while True:
    check_buttons_and_update_leds()
