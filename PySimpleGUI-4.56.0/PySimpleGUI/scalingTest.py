import PySimpleGUI as sg


# ------------------ Add following code block into your script ------------
def get_scaling():
    # called before window created
    root = sg.tk.Tk()
    scaling = root.winfo_fpixels('1i')/72
    root.destroy()
    return scaling

# Find the number in original screen when GUI designed.
my_scaling = 1.334646962233169      # call get_scaling()
my_width, my_height = 1536, 864     # call sg.Window.get_screen_size()

# Get the number for new screen
scaling_old = get_scaling()
width, height = sg.Window.get_screen_size()

scaling = scaling_old * min(width / my_width, height / my_height)

sg.set_options(scaling=scaling)
# -------------------------------------------------------------------------

layout = [
    [sg.Input('', key='-INPUT-', expand_x=True)],
    [sg.Push(), sg.Button('Exit')],
]
window = sg.Window("test", layout, finalize=True)

while True:
    event, values = window.read()
    if event in (sg.WINDOW_CLOSED, 'Exit'):
        break
    print(event, values)
window.close()