import tkinter as tk
from os import environ
from datetime import datetime as date


def open_file():
    # our ram file is always our most current file
    with open(ram_file, 'r') as ram:
        t.insert(tk.INSERT, ram.read()[:-1])  # -1 is to omit the extra line the program adds


# these files have to be opened at different times, which is why they are separated by function call

def open_settings():
    with open(config_file, 'r') as config:
        global geo
        geo = config.read().strip()

    with open(imm_config_file, 'r') as immc:
        global settings
        settings = {}

        for row in immc:
            if row[0] not in ['#', '\n']:
                x = row.split()
                settings[x[0][:-1]] = x[1]


def save():
    for file in backups_list:
        with open(file, 'w') as f:
            f.write(t.get('1.0', tk.END))

    with open(config_file, 'w') as config:
        config.write(
            '{}x{}'.format(str(root.winfo_width()), str(root.winfo_height()))
            +
            '+{}+{}'.format(str(root.winfo_rootx() + int(settings['rootx_adjust'])),
                            str(root.winfo_rooty() + int(settings['rooty_adjust'])))
        )


root = tk.Tk()
root.title('')  # default is 'tk', so we're opting out

# so no one can see my data :^) idea from david's emailing venture
template = environ['TRACKER_FILES'] + 'tracker_texts/1/{}'

# Setting up their file locations in order to be opened later
backup = template.format('backup' + str(date.today().isoweekday()) + '.txt')  # today's backup
ram_file = template.format('ram.txt')
config_file = template.format('configuration.txt')
imm_config_file = template.format('immutable_configuration.txt')
backups_list = [backup, ram_file]

open_settings()

# Styling the window and its widgets
root.geometry(geo)

frame1 = tk.Frame(root, bg=settings['bar_color'])  # no widgets attached, just provides the little rectangle
frame1.pack(pady=11)

t = tk.Text(root, bg=settings['bg_color'], fg=settings['font_color'],
            font=(settings['font_family'], int(settings['font_size']), settings['font_weight'].lower()),
            insertbackground=settings['font_color'], insertborderwidth=1, undo=True, maxundo=-1,
            padx=8, pady=2)
t.pack(expand=True, fill=tk.BOTH)
root.configure(background=settings['bar_color'])

open_file()

# So I can edit the python file indirectly
root.overrideredirect(settings['ORR'])
# Could probably put this line in save but I really don't want to as it would be ignored 99.999% of the time

# An autosave feature.
# q exists cause binding returns unnecessary data, just like how q is an unnecessary letter; needs to be put *somewhere*
t.bind('<KeyRelease>', lambda q: save())
# t.focus_set(), for focusing on this widget on startup

# Whenever you click the X button, automatically saves before closing itself
root.protocol('WM_DELETE_WINDOW', lambda: [save(), root.destroy()])

root.mainloop()
