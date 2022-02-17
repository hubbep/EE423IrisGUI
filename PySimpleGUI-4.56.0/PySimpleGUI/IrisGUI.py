# !/usr/bin/env python
import PySimpleGUI as sg
from PIL import Image
import PIL
import io
import base64
import os
import ctypes

G_SIZE = (820, 480)  # Size of the Graph in pixels. Using a 1 to 1 mapping of pixels to pixels
sg.theme('black')


def convert_to_bytes(file_or_bytes, resize=None):
    '''
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (str | bytes)
    :param resize:  optional new size
    :type resize: ((int, int) | None)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    '''
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))

    cur_width, cur_height = img.size
    if file_or_bytes != background_to_display:
        if cur_height != 480 or cur_width != 640:
            window['-DIMERROR-'].update('Warning: unexpected image dimension')
        else:
            window['-DIMERROR-'].update('')
    if resize:
        new_width, new_height = resize
        scale = min(new_height / cur_height, new_width / cur_width)
        img = img.resize((int(cur_width * scale), int(cur_height * scale)), PIL.Image.ANTIALIAS)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()


def draw_image_raw():
    file_to_display = os.path.join(folder, fnames[offset])
    window['-FILENAME-'].update(file_to_display)
    img_data = convert_to_bytes(file_to_display, resize=None)
    image_id = graph.draw_image(data=img_data, location=(0, G_SIZE[1]))
    return image_id


folder = sg.popup_get_folder('Where are your images?')
if not folder:
    exit(0)

file_list = os.listdir(folder)
fnames = [f for f in file_list if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp", ".gif", ".ico"))]
num_files = len(fnames)

graph = sg.Graph(canvas_size=G_SIZE, graph_bottom_left=(0, 0), graph_top_right=G_SIZE, enable_events=True, key='-GRAPH-', pad=(0, 0), change_submits=True, drag_submits=True)

col = [[sg.T('Choose what clicking a figure does', enable_events=True)],
       # Draw Oval needs to be implemented
       [sg.R('Draw Oval', 1, key='-OVAL-', enable_events=True)],
       [sg.R('Draw Line', 1, key='-LINE-', enable_events=True)],
       [sg.R('Draw points', 1, key='-POINT-', enable_events=True)],
       [sg.R('Erase item', 1, key='-ERASE-', enable_events=True)],
       # Erase selection needs to be implemented
       [sg.R('Erase selection', 1, key='-SELECT_ERASE-', enable_events=True)],
       [sg.R('Send to back', 1, key='-BACK-', enable_events=True)],
       [sg.R('Bring to front', 1, key='-FRONT-', enable_events=True)],
       [sg.R('Move Stuff', 1, key='-MOVE-', enable_events=True)],
       [sg.B('Save Image', key='-SAVE-')],
       ]

col_layout = [[sg.Text('Toolbar')],
              [sg.Button('-LEFT-')],
              [sg.Button('-ELSE-')],
              [sg.Button('-PUPILMASK-')]]

layout = [[sg.Text(f'Displaying image: '), sg.Text(k='-FILENAME-'), sg.Text('', k='-DIMERROR-')],
          [graph, sg.Column(col_layout)],
          [sg.Text('Developed for Clarkson Universtiy Biometric Department'), sg.Text(key='info', size=(60, 1))]]

window = sg.Window('Iris correction program', layout, margins=(0, 0), use_default_focus=False, finalize=True)

background_to_display = os.path.join(os.getcwd(), 'background.png')
background_data = convert_to_bytes(background_to_display, resize=G_SIZE)
background = graph.draw_image(data=background_data, location=(0, G_SIZE[1]))


offset, move_amount, tool = 0, 5, '-NONE-'
image_id = draw_image_raw()
dragging = False
start_point = end_point = prior_rect = None

while True:

    # program is paused here until window.read() completed?
    event: object
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
        
    if event == '-LEFT-':
        # FUNCTIONALITY TO BE IMPLEMENTED
        offset = (offset + (num_files - 1)) % num_files  # Decrement - roll over to MAX from 0
        graph.delete_figure(image_id)
        image_id = draw_image_raw()

    if event == '-ELSE-':
        # FUNCTIONALITY TO BE IMPLEMENTED
        offset = (offset + 1) % num_files  # Increment to MAX then roll over to 0
        graph.delete_figure(image_id)
        image_id = draw_image_raw()

    if event == '-PUPILMASK-':
        tool = '-PUPILMASK-'

    if event == '-GRAPH-' and tool == '-PUPILMASK-':  # if there's a "Graph" event, then it's a mouse
        x, y = values['-GRAPH-']
        if not dragging:
            start_point = (x, y)
            dragging = True
        else:
            end_point = (x, y)
        if prior_rect:
            graph.delete_figure(prior_rect)
        if None not in (start_point, end_point):
            prior_rect = graph.draw_oval(start_point, end_point, line_color='red')
    elif event.endswith('+UP'):  # The drawing has ended because mouse up
        info = window['info']
        info.update(value=f"grabbed rectangle from {start_point} to {end_point}")
        start_point, end_point = None, None  # enable grabbing a new rect
        dragging = False

window.close()
