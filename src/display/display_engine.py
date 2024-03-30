# NOTE: GPIO must be in GPIO.BCM mode for this to work
from threading import Thread, Lock
from src.display.TextBox import TextBox
from src.display.epd_driver import DisplayDriver
from PIL import ImageFont, ImageDraw, Image
from src.event import Event
from src.display.image_text import ImageText
import time

class DisplayEngine:
    """Utility functions for drawing on the ePaper display"""
    frame_buf: Image.Image = None # currently displayed image
    next_buf: Image.Image = None # Image to be displayed when data is flushed
    num_updates = 99 # first update should be global
    busy_event: Event = Event()
    busy_counter: int = 0 # TODO extract to globals
    has_scheduled_update = False
    thread: Thread = None
    lock = Lock()

    def increase_busy_counter():
        DisplayEngine.busy_counter = DisplayEngine.busy_counter + 1
        if DisplayEngine.busy_counter == 1:
            DisplayEngine.busy_event.fire(True)

    def decrease_busy_counter():
        DisplayEngine.busy_counter = DisplayEngine.busy_counter - 1
        if DisplayEngine.busy_counter == 0:
            DisplayEngine.busy_event.fire(False)

    def init():
        DisplayDriver.COG_initial()
        DisplayEngine.frame_buf = Image.new('1', (720, 256), 0x00)
        DisplayEngine.next_buf = Image.new('1', (720, 256), 0x00)
        DisplayEngine.thread = Thread(target=DisplayEngine.render_thread, name="displayEngine.render", daemon=True)
        DisplayEngine.thread.start()
    
    def clear_display():
        """draws the whole display white"""
        image_draw = ImageDraw.Draw(DisplayEngine.next_buf)
        DisplayEngine.lock.acquire()
        image_draw.rectangle((0, 0, 720, 256), 0x00)
        DisplayEngine.has_scheduled_update = True
        DisplayEngine.lock.release()

    def draw_rect(x: int, y: int, width: int, height: int):
        """Draws a white rectangle"""
        image_draw = ImageDraw.Draw(DisplayEngine.next_buf)
        DisplayEngine.lock.acquire()
        image_draw.rectangle((x, y, x + width, y + height), 0x00)
        DisplayEngine.has_scheduled_update = True
        DisplayEngine.lock.release()

    def draw_text(textbox: TextBox):
        """
        `draw_text` will split the text into lines, based on `textBox.width`.
        """
        drawer = ImageText(DisplayEngine.next_buf, mode='1')
        DisplayEngine.lock.acquire()
        ret = drawer.write_text_box((textbox.xc, textbox.yc), str(textbox.text), textbox.width,
        textbox.font, textbox.font_size, 0xFF, textbox.hAlign,
        line_spacing=textbox.line_spacing)
        DisplayEngine.has_scheduled_update = True
        DisplayEngine.lock.release()
        return ret
    
    def draw_simple_text(xc:int, yc:int, font_size:int, text:str):
        draw = ImageDraw.Draw(DisplayEngine.next_buf)
        font = ImageFont.truetype('assets/static/PlayfairDisplay-Regular.otf', font_size)
        DisplayEngine.lock.acquire()
        draw.text((xc, yc), text, font=font, fill=0xFF)
        DisplayEngine.has_scheduled_update = True
        DisplayEngine.lock.release()

    def render_thread():
        while True:
            if DisplayEngine.has_scheduled_update:
                time.sleep(0.15) # wait a bit to batch renders
                DisplayEngine.lock.acquire()# make sure that next_buf is not updated while here
                next_buf = DisplayEngine.next_buf.copy()
                DisplayEngine.has_scheduled_update = False
                DisplayEngine.lock.release()
                if DisplayEngine.num_updates > 14:
                    DisplayEngine.num_updates = 0
                    DisplayDriver.globalUpdate(next_buf.rotate(270, expand=True).tobytes(), DisplayEngine.frame_buf.rotate(270, expand=True).tobytes())
                else:
                    DisplayEngine.num_updates = DisplayEngine.num_updates + 1
                    DisplayDriver.fastUpdate(next_buf.rotate(270, expand=True).tobytes(), DisplayEngine.frame_buf.rotate(270, expand=True).tobytes())
                DisplayEngine.frame_buf = next_buf.copy()   
            time.sleep(0.01)

