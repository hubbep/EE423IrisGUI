# !/usr/bin/env python
import PySimpleGUI as sg
import numpy as np
from PIL import Image
import PIL
import io
import base64
import os

screen_width, screen_height = sg.Window.get_screen_size()
G_SIZE = (screen_width-400, screen_height-200)  # Size of the Graph in pixels. Using a 1 to 1 mapping of pixels to pixels
sg.theme('black')

'''
CLASS TO ACCESS MASK DATA AND LOGIC
'''


class ovalMask:
    """
    Note: error handling of object when object does not exist (aka. data is still None) needs to be implemented
    """
    def __init__(self, top_left=None, bottom_right=None, h=None, k=None, a=None, b=None, plot_ID = None):
        self.center = (h, k)
        self.width = a
        self.height = b
        self.topLeft = top_left
        self.bottomRight = bottom_right
        self.plotID = plot_ID

    def __del__(self):
        print("Deleting ovalMask obj")

    def get_width(self):
        a = (self.bottomRight[0] - self.topLeft[0]) / 2
        self.width = a
        return a

    def get_height(self):
        b = (self.bottomRight[1] - self.topLeft[1]) / 2
        self.height = b
        return b

    def get_center(self):
        self.get_width()
        self.get_height()
        h = self.topLeft[0] + self.width
        k = self.topLeft[1] + self.height
        self.center = (h, k)
        return h, k

    def check_inside(self, point=(0, 0)):
        self.get_center()
        result = (pow((point[0] - self.center[0]), 2) / pow(self.width, 2)) + (pow((point[1] - self.center[1]), 2) / pow(self.height, 2))
        if result <= 1:
            return True
        else:
            return False

    def get_plotID(self):
        self.plotID = graph.draw_oval(start_point, end_point, line_color='red')
        return self.plotID


# COULD POTENTIALLY IMPLEMENT ARC MASK TO MASK EYELIDS
# class arcMask():


'''
CLASS TO ACCESS IMAGE DATA AND LOGIC
'''


class imageProcessing:
    def __init__(self, file_or_bytes=None, resize=None, scale=None, img=None, plot_id=None):
        self.org_width = None
        self.org_height = None
        self.fileOrBytes = file_or_bytes
        self.resize = resize
        self.scale = scale
        self.img = img
        self.file = None
        self.plotID = plot_id
        self.get_img()
        self.resize_img()

    def __del__(self):
        print("Deleting imageProcessing obj")

    def get_isfile(self):
        if isinstance(self.fileOrBytes, str):
            self.file = self.fileOrBytes
            return True
        else:
            self.file = None
            return False

    def get_img(self):
        """
        FUNCTION ONLY MEANT TO BE USED WHEN file_or_bytes GIVEN
        (Error handling for missing fileOrBytes could be implemented)
        """
        if self.img is not None:
            return self.img
        else:
            if self.get_isfile():
                img = PIL.Image.open(self.fileOrBytes)
            else:
                img = PIL.Image.open(io.BytesIO(base64.b64decode(self.fileOrBytes)))
            self.img = img
            return self.img

    def resize_img(self):
        """
        FUNCTION RESIZES IMAGE WHILE PRESERVING SCALE
        (The whole purpose of this class is to preserve variables for use in other functions)
        """
        if self.org_width is None or self.org_height is None:
            self.org_width, self.org_height = self.img.size
        cur_width, cur_height = self.img.size
        if self.resize:
            new_width, new_height = self.resize
            self.scale = min(new_height / cur_height, new_width / cur_width)
            self.img = self.img.resize((int(cur_width * self.scale), int(cur_height * self.scale)), PIL.Image.ANTIALIAS)
        if self.scale:
            self.img = self.img.resize((int(cur_width * self.scale), int(cur_height * self.scale)), PIL.Image.ANTIALIAS)

    def draw_image_raw(self):
        self.get_img()
        if self.resize:
            self.resize_img()
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        self.plotID = graph.draw_image(data=bio.getvalue(), location=(0, G_SIZE[1]))
        return self.plotID


'''
OTHER FUNCTIONS
'''


# def save_element_as_file(element, filename):
#     """
#     Saves any element as an image file.  Element needs to have an underlyiong Widget available (almost if not all of them do)
#     :param element: The element to save
#     :param filename: The filename to save to. The extension of the filename determines the format (jpg, png, gif, ?)
#     """
#     widget = element.Widget
#     box = (widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_rootx() + widget.winfo_width(),
#            widget.winfo_rooty() + widget.winfo_height())
#     grab = ImageGrab.grab(bbox=box)
#     grab.save(filename)


def export_mask():
    filename_prefix = os.path.splitext(image_id.file)[0]
    filename_suffix = "mask.jpg"
    filename = os.path.join(folder, filename_prefix + "_" + filename_suffix)
    cur_width, cur_height = image_id.img.size

    array = np.zeros(shape=(cur_height, cur_width, 3), dtype=np.uint8)

    for k in range(0, cur_height, 1):
        for h in range(0, cur_width, 1):
            if inner_mask.check_inside(point=(h, k)) is True:
                array[k, h] = [0, 0, 0]
            elif outer_mask.check_inside(point=(h, k)) is False:
                array[k, h] = [0, 0, 0]
            else:
                array[k, h] = [255, 255, 255]

    array = np.flip(array, axis=0)

    # Use PIL to create an image from the new array of pixels
    new_image = Image.fromarray(array)
    new_image = new_image.resize(size=(image_id.org_width, image_id.org_height))
    new_image.save(filename)


'''
# ---- INIT SECTION ----    ---- INIT SECTION ----    ---- INIT SECTION ----    ---- INIT SECTION ----
'''
folder = sg.popup_get_folder('Where are your images?')
if not folder:
    exit(0)
file_list = os.listdir(folder)
fnames = [f for f in file_list if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(
    (".png", ".jpg", "jpeg", ".tiff", ".bmp", ".gif", ".ico"))]
num_files = len(fnames)
graph = sg.Graph(canvas_size=G_SIZE, graph_bottom_left=(0, 0), graph_top_right=G_SIZE, enable_events=True,
                 key='-GRAPH-', pad=(0, 0), change_submits=True, drag_submits=True, background_color='grey')

'''
# ---- LAYOUT SECTION ----    ---- LAYOUT SECTION ----    ---- LAYOUT SECTION ----    ---- LAYOUT SECTION ----
'''
col = [[sg.T('GRAPH TOOLS', enable_events=True)],
       # Draw Oval needs to be modified for better usability
       [sg.R('Draw Oval - inner iris', 1, key='-IN-OVAL-', enable_events=True)],
       [sg.R('Draw oval - outer iris', 1, key='-OUT-OVAL-', enable_events=True)],
       # [sg.R('Draw points', 1, key='-POINT-', enable_events=True)],
       # [sg.R('Erase item', 1, key='-ERASE-', enable_events=True)],
       # Erase selection needs to be implemented
       # [sg.R('Erase selection', 1, key='-SELECT_ERASE-', enable_events=True)],
       # [sg.R('Send to back', 1, key='-BACK-', enable_events=True)],
       # [sg.R('Bring to front', 1, key='-FRONT-', enable_events=True)],
       # [sg.R('Move Stuff', 1, key='-MOVE-', enable_events=True)],
       [sg.T('FILE TOOLS', enable_events=True)],
       [sg.B('Previous Image', key='-PREV-'), sg.B('Next Image', key='-NEXT-')],
       [sg.B('Save Mask', key='-SAVE-')],
       ]
layout = [[sg.Text(f'Displaying image: '), sg.Text(k='-FILENAME-'), sg.Text('', k='-DIMERROR-')],
          [graph, sg.Column(col)],
          [sg.Text('Developed for Clarkson Universtiy Biometric Department'), sg.Text(key='info', size=(60, 1))]]
window = sg.Window('Iris correction program', layout, margins=(0, 0), use_default_focus=False, finalize=True)

'''
# ---- LOGIC SECTION ----    ---- LOGIC SECTION ----    ---- LOGIC SECTION ----    ---- LOGIC SECTION ----
'''
# background_to_display = os.path.join(os.getcwd(), 'background.png')
# background = imageProcessing(file_or_bytes=background_to_display, resize=G_SIZE)
# background.draw_image_raw()

offset, move_amount, tool, inner_mask, outer_mask = 0, 5, '-NONE-', ovalMask(), ovalMask()
file_to_display = os.path.join(folder, fnames[offset])
window['-FILENAME-'].update(file_to_display)
image_id = imageProcessing(file_or_bytes=file_to_display, resize=G_SIZE)
image_id.draw_image_raw()
dragging = False
start_point = end_point = prior_rect = None

while True:
    event: object
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break

    if event == '-PREV-':
        # FUNCTIONALITY TO BE IMPLEMENTED
        offset = (offset + (num_files - 1)) % num_files  # Decrement - roll over to MAX from 0
        graph.erase()
        file_to_display = os.path.join(folder, fnames[offset])
        window['-FILENAME-'].update(file_to_display)
        image_id = imageProcessing(file_or_bytes=file_to_display, resize=G_SIZE)
        image_id.draw_image_raw()

    if event == '-NEXT-':
        # FUNCTIONALITY TO BE IMPLEMENTED
        offset = (offset + 1) % num_files  # Increment to MAX then roll over to 0
        graph.erase()
        file_to_display = os.path.join(folder, fnames[offset])
        window['-FILENAME-'].update(file_to_display)
        image_id = imageProcessing(file_or_bytes=file_to_display, resize=G_SIZE)
        image_id.draw_image_raw()

    # if event == '-MASK-':
    #     print("To be implemented")

    if event == '-SAVE-':
        print("Saving graph")
        export_mask()

    if event == '-IN-OVAL-':
        tool = '-IN-OVAL-'

    if event == '-OUT-OVAL-':
        tool = '-OUT-OVAL-'

    if event == '-GRAPH-' and (
            tool == '-IN-OVAL-' or tool == '-OUT-OVAL-'):  # if there's a "Graph" event that requires a drag select
        x, y = values['-GRAPH-']
        if not dragging:
            start_point = (x, y)
            dragging = True
        else:
            end_point = (x, y)
        if prior_rect:
            graph.delete_figure(prior_rect)
        if None not in (start_point, end_point):
            prior_rect = graph.draw_rectangle(start_point, end_point, line_color='red')
    elif event.endswith('+UP'):  # The drawing has ended because mouse up
        info = window['info']
        info.update(value=f"grabbed rectangle from {start_point} to {end_point}")
        if tool == '-IN-OVAL-':
            if inner_mask.plotID:
                graph.delete_figure(inner_mask.plotID)
            del inner_mask
            inner_mask = ovalMask(top_left=start_point, bottom_right=end_point)
            inner_mask.get_plotID()
        if tool == '-OUT-OVAL-':
            if outer_mask.plotID:
                graph.delete_figure(outer_mask.plotID)
            del outer_mask
            outer_mask = ovalMask(top_left=start_point, bottom_right=end_point)
            outer_mask.get_plotID()
        start_point, end_point = None, None  # enable grabbing a new rect
        dragging = False

window.close()
