import PySimpleGUI as sg

"class someClass(sg):"
"{"
"   sg.__init__(self):"
"}"

sg.main()

sg.theme("DarkBlue")
sg.set_options(font=('Courier New', 16))

layout = [
    [sg.Multiline('', size=(40, 5), enable_events=True, key='M1')],
    [sg.Multiline('', size=(40, 5), key='M2')],
]
window = sg.Window("Title", layout, finalize=True)

m1, m2 = window["M1"], window['M2']
m2.bind("<Return>", "_Return")

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    elif event == "M1" and 'jk' in values["M1"]:
        m1.Widget.delete("insert-2c", "insert")
        m2.set_focus()
    elif event == "M2_Return":
        m1.set_focus()
    print(event, values)

window.close()