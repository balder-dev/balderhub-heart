import random
from typing import Union
import sys
import math
import time
import multiprocessing
import tkinter as tk
from .utils import ColorConfiguration, Command

FREQUENCY_MONITOR = 60

def process_target_func(   # pylint: disable=too-many-statements
        send_queue: multiprocessing.Queue,
        recv_queue: multiprocessing.Queue,
        position: tuple[int, int],
        size: tuple[int, int],
        color_config: ColorConfiguration
) -> None:
    """
    Processed method that handles the full graphical process
    :param send_queue: queue to send confirmation messages/answers
    :param recv_queue: queue to receive new commands
    :param position: x, y tuple with the position information
    :param size: width, height tuple with the size information
    :param color_config: the color configuration that should be used for the simulation
    """
    root = tk.Tk()
    root.geometry(f"{size[0]}x{size[1]}+{position[0]}+{position[1]}")
    root.title("BalderHub Heart Optical Simulator")
    root.overrideredirect(True)  # without border
    root.attributes('-topmost', True)
    root.update_idletasks()

    canvas = tk.Canvas(root, width=size[0], height=size[1], bg='white', highlightthickness=0)
    canvas.pack()

    # None: alpha 100% (no skin contact) | -1: currently a sleep (alpha 0%) -> start counting on next awakening
    index: Union[int, None] = None
    current_bpm = 60
    flashing = False

    # Rechteck mit fester Größe erstellen
    rect = canvas.create_rectangle(0, 0, size[0], size[1], fill='white')

    start_time = None
    # TODO improve frequency

    def iteration():
        nonlocal index
        nonlocal start_time
        nonlocal flashing

        length_full_beat_ms = (60 / current_bpm) * 1000

        if index is None:
            # stop iteration
            canvas.itemconfig(rect, fill=color_config.get_color(1))
            return

        # calculate color according sin()
        if index == 0:
            start_time = time.perf_counter()


        phase = ((time.perf_counter() - start_time) * 1000 / length_full_beat_ms) * 2 * math.pi

        if flashing:
            red = random.randint(0, 255)
            green = random.randint(0, 255)
            blue = random.randint(0, 255)
            color = f'#{red:02x}{green:02x}{blue:02x}'
        else:
            alpha = 0.5 * math.sin(phase) + 0.5 # scale alpha between 0...1
            color = color_config.get_color(alpha)

        canvas.itemconfig(rect, fill=color)
        canvas.after(int(1000 / FREQUENCY_MONITOR), iteration)
        index += 1

    # Starte mit kleinem Delay
    root.after(100, iteration)

    def check_queue():
        nonlocal current_bpm
        nonlocal index
        nonlocal flashing

        while not recv_queue.empty():
            cmd, kwargs = recv_queue.get_nowait()
            if cmd == Command.SET_BPM:
                current_bpm = kwargs['bpm']
                send_queue.put(None)
            if cmd == Command.START:
                index = 0
                canvas.after(10, iteration)
                send_queue.put(None)
            if cmd == Command.STOP:
                index = None
                send_queue.put(None)
            if cmd == Command.GET_BPM:
                send_queue.put(current_bpm)
            if cmd == Command.IS_ACTIVE:
                send_queue.put(index is not None)
            if cmd == Command.ENABLE_FLASHING:
                flashing = True
                send_queue.put(None)
            if cmd == Command.DISABLE_FLASHING:
                flashing = False
                send_queue.put(None)
            if cmd == Command.IS_FLASHING_ENABLED:
                send_queue.put(flashing)
            if cmd == Command.QUIT:
                root.quit()
                sys.exit(0)

        root.after(100, check_queue)  # recheck queue every 100ms

    check_queue()

    root.mainloop()
