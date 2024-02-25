import time
from PIL import Image, ImageSequence


def show_gif(display, gif_path, display_time=10, frame_duration=0.1):
    start_time = time.time()

    gif = Image.open(gif_path)

    while time.time() - start_time < display_time:
        for frame in ImageSequence.Iterator(gif):
            image = frame.convert("RGB")
            try:
                display.display(image)
                display.show()
            except AssertionError as e:
                print(f"AssertionError: {e}")
                print(f"Image mode: {image.mode}, OLED mode: {display.mode}")
            time.sleep(frame_duration)  # Adjust the sleep time to control the animation speed
