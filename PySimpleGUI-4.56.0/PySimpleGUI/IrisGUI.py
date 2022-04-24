# !/usr/bin/env python3.9


import PySimpleGUI as sg
import numpy as np
from PIL import Image
import PIL
import io
import base64
import configparser
import os
import shutil
from os.path import exists
Config = configparser.ConfigParser()


def config_section_map(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
        except Config.DoesNotExist:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


class ProgramInitialize:
    def __init__(self):
        self.orgFolder = 'None'
        self.segFolder = 'None'
        self.maskFolder = 'None'
        self.lastImage = 'None'
        self.fileNames = None
        self.index = 0
        self.prog_init_config()

    def prog_init_config(self):
        """
        Reads / creates config file state.ini
        Initializes variables from state.ini if present
        Determines all folder locations exist
        Populates filenames with images that exist in all folders
        """
        for section in Config.sections():
            Config.remove_section(section)
        config_file_location = os.path.join(os.getcwd(), 'state.ini')
        if exists(config_file_location):
            Config.read(config_file_location)
        if 'lastimage' not in Config.sections():
            Config.add_section('lastimage')
            Config.set('lastimage', 'filename', self.lastImage)
        else:
            self.lastImage = config_section_map('lastimage')['filename'].replace("\\","/")
            self.lastImage = os.path.basename(self.lastImage)
        if 'filelocations' not in Config.sections():
            Config.add_section('filelocations')
            self.get_folders()
            Config.set('filelocations', 'orgfolder', self.orgFolder)
            Config.set('filelocations', 'segfolder', self.segFolder)
            Config.set('filelocations', 'maskfolder', self.maskFolder)
        else:
            self.orgFolder = config_section_map('filelocations')['orgfolder']
            self.segFolder = config_section_map('filelocations')['segfolder']
            self.maskFolder = config_section_map('filelocations')['maskfolder']
            self.get_folders()

        cfgfile = open(config_file_location, 'w')
        Config.write(cfgfile)
        cfgfile.close()

        if exists(self.orgFolder) is False or exists(self.segFolder) is False or exists(self.maskFolder) is False:
            exit(2)

        file_list = os.listdir(self.orgFolder)
        self.fileNames = \
            [f for f in file_list if os.path.isfile(os.path.join(self.orgFolder, f)) and
                os.path.isfile(os.path.join(self.segFolder, f)) and
                os.path.isfile(os.path.join(self.maskFolder, f)) and
                f.lower().endswith((".png", ".jpg", "jpeg", ".tiff", ".bmp", ".gif", ".ico"))]
        if self.lastImage != 'None':
            self.index = self.fileNames.index(self.lastImage)

    def get_folders(self):
        if self.orgFolder == 'None':
            self.orgFolder = sg.popup_get_folder('Where are your original images?')
            Config.set('filelocations', 'orgfolder', self.orgFolder)
        if self.segFolder == 'None':
            self.segFolder = sg.popup_get_folder('Where are your segmented images?')
            Config.set('filelocations', 'segfolder', self.segFolder)
        if self.maskFolder == 'None':
            self.maskFolder = sg.popup_get_folder('Where are your masked images?')
            Config.set('filelocations', 'maskfolder', self.maskFolder)
        if self.orgFolder == 'None' or self.segFolder == 'None' or self.maskFolder == 'None':
            print("Problem reading folder locations")
            exit(2)


class OvalMask:
    """
    CLASS TO ACCESS MASK DATA AND LOGIC
    Note: error handling of object when object does not exist (aka. data is still None) needs to be implemented
    """
    def __init__(self, top_left=None, bottom_right=None, h=None, k=None, a=None, b=None, plot_id=None):
        self.center = (h, k)
        self.width = a
        self.height = b
        self.topLeft = top_left
        self.bottomRight = bottom_right
        self.plotID = plot_id

    def __del__(self):
        print("Deleting OvalMask obj")

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
        result = \
            (pow((point[0] - self.center[0]), 2) / pow(self.width, 2)) + \
            (pow((point[1] - self.center[1]), 2) / pow(self.height, 2))
        if result <= 1:
            return True
        else:
            return False

    def get_plotid(self):
        self.plotID = graph.draw_oval(start_point, end_point, line_color='red')
        return self.plotID


class DragHistory:
    def __init__(self, point_size=None):
        self.dragPoints = tuple()
        self.pointSize = point_size

    def add_point(self, point=tuple()):
        self.dragPoints = self.dragPoints + point


class PointsHistory:
    def __init__(self):
        self.dragPaths = None

    def add_path(self, drag_path=None):
        self.dragPaths = self.dragPaths + drag_path

# COULD POTENTIALLY IMPLEMENT ARC MASK TO MASK EYELIDS
# class arcMask():


# class pointsMask(ovalMask):
#     '''
#     CLASS FOR CAPTURING DRAWN POINTS
#     '''
#     def __init__(self, center=(None, None), radius=None):
#         h, k = center
#         super.__init__(self, h=h, k=k, a=radius, b=radius)


class ImageProcessing:
    """
    CLASS TO ACCESS IMAGE DATA AND LOGIC
    Note: error handling of object when object does not exist (aka. data is still None) needs to be implemented
    """
    def __init__(self, file_or_bytes=None, resize=None, scale=None, img=None, plot_id=None):
        self.array = None
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
        print("Deleting ImageProcessing obj")

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
            width, height = self.img.size
            self.array = np.full(shape=(height, width, 3), fill_value=255, dtype=np.uint8)
            return self.img
        else:
            if self.get_isfile():
                img = PIL.Image.open(self.fileOrBytes)
            else:
                img = PIL.Image.open(io.BytesIO(base64.b64decode(self.fileOrBytes)))
            self.img = img
            width, height = self.img.size
            self.array = np.full(shape=(height, width, 3), fill_value=255, dtype=np.uint8)
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
        elif self.scale:
            self.img = self.img.resize((int(cur_width * self.scale), int(cur_height * self.scale)), PIL.Image.ANTIALIAS)

    def draw_image_raw(self):
        graph.change_coordinates((0, 0), G_SIZE)
        self.get_img()
        cur_width, cur_height = self.img.size
        if self.resize:
            self.resize_img()
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        self.plotID = graph.draw_image(data=bio.getvalue(), location=(0, G_SIZE[1]))
        graph.change_coordinates((0, (cur_height - G_SIZE[1])), (G_SIZE[0], cur_height))
        return self.plotID

    def draw_seg_image_raw(self):
        self.get_img()
        if self.resize:
            self.resize_img()
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        self.plotID = graphseg.draw_image(data=bio.getvalue(), location=(0, GVIEW_SIZE[1]))
        return self.plotID

    def draw_mask_image_raw(self):
        self.get_img()
        if self.resize:
            self.resize_img()
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        self.plotID = graphmask.draw_image(data=bio.getvalue(), location=(0, GVIEW_SIZE[1]))
        return self.plotID

    def export_mask(self):
        self.get_isfile()
        filename_prefix = os.path.basename(self.file)
        # filename_prefix = os.path.splitext(filename_prefix)[0]
        filename_suffix = "reviewed.jpg"
        # filename = os.path.join(program.maskFolder, filename_prefix + "_" + filename_suffix)
        filename = os.path.join(program.maskFolder, filename_prefix)
        filename2 = os.path.join(program.maskFolder, filename_prefix + "_" + filename_suffix)
        cur_width, cur_height = self.img.size

        for k in range(0, cur_height, 1):
            for h in range(0, cur_width, 1):
                if inner_mask.check_inside(point=(h, k)) is True:
                    self.array[k, h] = [0, 0, 0]
                elif outer_mask.check_inside(point=(h, k)) is False:
                    self.array[k, h] = [0, 0, 0]
                else:
                    self.array[k, h] = [255, 255, 255]

        self.array = np.flip(self.array, axis=0)

        # Use PIL to create an image from the new array of pixels
        new_image = Image.fromarray(self.array)
        new_image = new_image.resize(size=(image_id.org_width, image_id.org_height))
        new_image.save(filename)
        new_image.save(filename2)

    # def img_init_config(self):
    #     for section in Config.sections():
    #         Config.remove_section(section)
    #     config_file_location = self.file
    #     if exists(config_file_location):
    #         Config.read(config_file_location)
    #     else:
    #         org_folder, seg_folder, mask_folder = get_folders()
    #         Config.add_section('inneriris')
    #         Config.set('inneriris', 'topleft', inner_mask.topLeft)
    #         Config.set('inneriris', 'bottomright', inner_mask.bottomRight)
    #
    #         Config.add_section('outeriris')
    #         Config.set('outeriris', 'topleft', inner_mask.topLeft)
    #         Config.set('outeriris', 'bottomright', inner_mask.bottomRight)
    #
    #         cfgfile = open(config_file_location, 'w')
    #         Config.write(cfgfile)
    #         cfgfile.close()
    #     # res = tuple(map(int, test_str.split(', ')))


'''
# ---- INIT SECTION ----    ---- INIT SECTION ----    ---- INIT SECTION ----    ---- INIT SECTION ----
'''
program = ProgramInitialize()
screen_width, screen_height = sg.Window.get_screen_size()
G_SIZE = (screen_width-800, screen_height-200)
GVIEW_SIZE = (200, 200)
sg.theme('black')

# TO DO
num_files = len(program.fileNames)
print(num_files)

graph = sg.Graph(canvas_size=G_SIZE, graph_bottom_left=(0, 0), graph_top_right=G_SIZE, enable_events=True,
                 key='-GRAPH-', pad=(0, 0), change_submits=True, drag_submits=True, background_color='grey')

graphseg = \
    sg.Graph(canvas_size=GVIEW_SIZE, graph_bottom_left=(0, 0), graph_top_right=GVIEW_SIZE,
             key='-GRAPHSEG-', pad=(0, 0), background_color='black')

graphmask = \
    sg.Graph(canvas_size=GVIEW_SIZE, graph_bottom_left=(0, 0), graph_top_right=GVIEW_SIZE,
             key='-GRAPHMASK-', pad=(0, 0), background_color='black')

'''
# ---- LAYOUT SECTION ----    ---- LAYOUT SECTION ----    ---- LAYOUT SECTION ----    ---- LAYOUT SECTION ----
'''
col = [[sg.T('SEGMENTATION PREVIEW', enable_events=True)],
       [graphseg],
       [sg.T('MASK PREVIEW', enable_events=True)],
       [graphmask],
       [sg.B('Accept Mask', key='-ACCEPT-')],
       ]

col2 = [[sg.T('GRAPH TOOLS', enable_events=True)],
        [sg.R('Draw oval - inner iris', 1, key='-IN-OVAL-', enable_events=True)],
        [sg.R('Draw oval - outer iris', 1, key='-OUT-OVAL-', enable_events=True)],
        [sg.R('Draw points', 1, key='-POINTS-', enable_events=True)],
        [sg.R('Erase - inner iris', 1, key='-ERASE-INNER-', enable_events=True)],
        [sg.R('Erase - outer iris', 1, key='-ERASE-OUTER-', enable_events=True)],
        [sg.R('Erase all', 1, key='-CLEAR-', enable_events=True)],
        [sg.B('Undo Points', key='-UNDO_P-')],
        # [sg.R('Send to back', 1, key='-BACK-', enable_events=True)],
        # [sg.R('Bring to front', 1, key='-FRONT-', enable_events=True)],
        # [sg.R('Move Stuff', 1, key='-MOVE-', enable_events=True)],
        [sg.T('FILE TOOLS', enable_events=True)],
        [sg.B('Previous Image', key='-PREV-'), sg.B('Next Image', key='-NEXT-')],
        [sg.B('Save Mask', key='-SAVE-')],
        ]

layout = [[sg.Text(f'Displaying image: '), sg.Text(k='-FILENAME-'), sg.Text('', k='-DIMERROR-')],
          [graph, sg.Column(col), sg.Column(col2)],
          [sg.Text('Developed for Clarkson Universtiy Biometric Department'), sg.Text(key='info', size=(60, 1))]]
window = sg.Window('Iris correction program', layout, margins=(0, 0), use_default_focus=False, finalize=True)

'''
# ---- LOGIC SECTION ----    ---- LOGIC SECTION ----    ---- LOGIC SECTION ----    ---- LOGIC SECTION ----
'''
# background_to_display = os.path.join(os.getcwd(), 'background.png')
# background = ImageProcessing(file_or_bytes=background_to_display, resize=G_SIZE)
# background.draw_image_raw()

tool, inner_mask, outer_mask = '-NONE-', OvalMask(), OvalMask()
orgfile_to_display = os.path.join(program.orgFolder, program.fileNames[program.index])
segfile_to_display = os.path.join(program.segFolder, program.fileNames[program.index])
maskfile_to_display = os.path.join(program.maskFolder, program.fileNames[program.index])
window['-FILENAME-'].update(orgfile_to_display)
image_id = ImageProcessing(file_or_bytes=orgfile_to_display, resize=G_SIZE)
image_id.draw_image_raw()
seg_image_id = ImageProcessing(file_or_bytes=segfile_to_display, resize=GVIEW_SIZE)
seg_image_id.draw_seg_image_raw()
mask_image_id = ImageProcessing(file_or_bytes=maskfile_to_display, resize=GVIEW_SIZE)
mask_image_id.draw_mask_image_raw()
dragging = False
start_point = end_point = prior_rect = None

while True:
    event: object
    event, values = window.read()
    # This is cool but how is order determined?
    print(event, values)
    if event == sg.WIN_CLOSED:
        break

    if event == '-PREV-':
        # FUNCTIONALITY TO BE IMPLEMENTED
        program.index = (program.index + (num_files - 1)) % num_files  # Decrement - roll over to MAX from 0
        graph.erase()
        orgfile_to_display = os.path.join(program.orgFolder, program.fileNames[program.index])
        segfile_to_display = os.path.join(program.segFolder, program.fileNames[program.index])
        maskfile_to_display = os.path.join(program.maskFolder, program.fileNames[program.index])
        window['-FILENAME-'].update(orgfile_to_display)
        image_id = ImageProcessing(file_or_bytes=orgfile_to_display, resize=G_SIZE)
        image_id.draw_image_raw()
        seg_image_id = ImageProcessing(file_or_bytes=segfile_to_display, resize=GVIEW_SIZE)
        seg_image_id.draw_seg_image_raw()
        mask_image_id = ImageProcessing(file_or_bytes=maskfile_to_display, resize=GVIEW_SIZE)
        mask_image_id.draw_mask_image_raw()

    if event == '-NEXT-':
        # FUNCTIONALITY TO BE IMPLEMENTED
        program.index = (program.index + 1) % num_files  # Increment to MAX then roll over to 0
        graph.erase()
        orgfile_to_display = os.path.join(program.orgFolder, program.fileNames[program.index])
        segfile_to_display = os.path.join(program.segFolder, program.fileNames[program.index])
        maskfile_to_display = os.path.join(program.maskFolder, program.fileNames[program.index])
        window['-FILENAME-'].update(orgfile_to_display)
        image_id = ImageProcessing(file_or_bytes=orgfile_to_display, resize=G_SIZE)
        image_id.draw_image_raw()
        seg_image_id = ImageProcessing(file_or_bytes=segfile_to_display, resize=GVIEW_SIZE)
        seg_image_id.draw_seg_image_raw()
        mask_image_id = ImageProcessing(file_or_bytes=maskfile_to_display, resize=GVIEW_SIZE)
        mask_image_id.draw_mask_image_raw()

    if event == '-SAVE-':
        print("Saving graph")
        image_id.export_mask()
        for section in Config.sections():
            Config.remove_section(section)
        config_file_location = os.path.join(os.getcwd(), 'state.ini')
        Config.read(config_file_location)
        if 'lastimage' in Config.sections():
            Config.set('lastimage', 'filename', image_id.file)
        else:
            Config.add_section('lastimage')
            Config.set('lastimage', 'filename', image_id.file)
        cfgfile = open(config_file_location, 'w')
        Config.write(cfgfile)
        cfgfile.close()

    if event == '-ACCEPT-':
        print("Mask Accepted")
        f_loc = mask_image_id.file
        f_name = os.path.basename(mask_image_id.file)
        split_f_name = os.path.splitext(f_name)
        new_f_name = split_f_name[0]+"_accepted"
        recon_f_name = f_loc.replace(split_f_name[0], new_f_name)

        shutil.copyfile(f_loc,recon_f_name)
        #print(mask_image_id.file)

    if event == '-IN-OVAL-':
        tool = '-IN-OVAL-'

    if event == '-OUT-OVAL-':
        tool = '-OUT-OVAL-'

    if values['-ERASE-INNER-']:
        graph.delete_figure(inner_mask.plotID)
        graph.delete_figure(prior_rect)
    if values['-ERASE-OUTER-']:
        graph.delete_figure(outer_mask.plotID)
        graph.delete_figure(prior_rect)
    if values['-CLEAR-']:
        graph.delete_figure(inner_mask.plotID)
        graph.delete_figure(outer_mask.plotID)
        graph.delete_figure(prior_rect)

    if event == '-GRAPH-' and (
            tool == '-IN-OVAL-' or tool == '-OUT-OVAL-' or
            tool == '-DRAW_P-'):  # if there's a "Graph" event that requires a drag select
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
            inner_mask = OvalMask(top_left=start_point, bottom_right=end_point)
            inner_mask.get_plotid()
        if tool == '-OUT-OVAL-':
            if outer_mask.plotID:
                graph.delete_figure(outer_mask.plotID)
            del outer_mask
            outer_mask = OvalMask(top_left=start_point, bottom_right=end_point)
            outer_mask.get_plotid()
        if values['-POINT-']:
            graph.draw_point((x, y), size=8)

        start_point, end_point = None, None  # enable grabbing a new rect
        dragging = False

window.close()
