import smbus
import time


MCP23017_IODIRA = 0x00  # I/O direction register for Port A
MCP23017_IODIRB = 0x01  # I/O direction register for Port B
MCP23017_GPIOA = 0x12   # Register for outputs on Port A
MCP23017_GPIOB = 0x13   # Register for outputs on Port B
MCP23017_GPPUA = 0x0C   # Pull-up resistors configuration for Port A
MCP23017_GPPUB = 0x0D   # Pull-up resistors configuration for Port B
MCP23017_ADDRESS = 0x27

print("Configuring MCP23017 I/O expander.")

bus = smbus.SMBus(1)
print(f"SMBus initialized")

bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRB, 0x3C)  # 0b00111100 - PB0-PB1 as output, PB2-PB5 as input
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPPUB, 0x3C)   # Enable pull-ups for PB2-PB5
bus.write_byte_data(MCP23017_ADDRESS, MCP23017_IODIRA, 0x00)  # Outputs: PA0-PA7

print("MCP23017 ports configured.")

prev_buttons = [0 for _ in range(8)]


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
    bus.write_byte_data(MCP23017_ADDRESS, MCP23017_GPIOA, led_state)


VOLUMIO_STATE_TO_LED = {
    'play': 0b00000001,  # Example LED pattern for play state
    'stop': 0b00000010,  # Example LED pattern for stop state
}


def update_leds_with_volumio_state(volumio_state):
    if volumio_state:
        status = volumio_state.get('status')
        led_pattern = VOLUMIO_STATE_TO_LED.get(status, 0)
        control_leds(led_pattern)


def check_buttons_and_update_leds(button_action_map) -> None:
    global prev_buttons
    buttons = read_button_matrix()
    for button_id in range(8):
        current_button_state = buttons[button_id]
        if current_button_state == 0 and prev_buttons[button_id] != current_button_state:
            print(f"Button {button_id} pressed")
            control_leds(1 << (button_id))
            if button_id in button_action_map:
                button_action_map[button_id]()
        prev_buttons[button_id] = current_button_state
        time.sleep(0.05)
