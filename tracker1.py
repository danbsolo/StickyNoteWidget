import tkinter as tk
from os import environ
from datetime import datetime as date


class StickyNoteWidget:
    def __init__(self, parent):

        self.parent = parent
        parent.title('') # default is 'tk', so we're opting out

        # so no one can see my data :^) idea from david's emailing venture
        template = environ['TRACKER_FILES'] + 'tracker_texts/1/{}'

        # Setting up their file locations in order to be opened later
        self.backup = template.format('backup' + str(date.today().isoweekday()) + '.txt')
        # today's backup
        self.ram_file = template.format('ram.txt')
        self.config_file = template.format('configuration.txt')
        self.imm_config_file = template.format('immutable_configuration.txt')
        self.backups_list = [self.backup, self.ram_file]

        self.open_settings()

        # Styling the window and its widgets
        self.parent.geometry(self.geo)

        frame1 = tk.Frame(root, bg=self.settings['bar_color'])  # no widgets attached, just provides the little rectangle
        frame1.pack(pady=11)

        self.t = tk.Text(root, bg=self.settings['bg_color'], fg=self.settings['font_color'],
            font=(self.settings['font_family'], int(self.settings['font_size']), self.settings['font_weight'].lower()),
            insertbackground=self.settings['font_color'], insertborderwidth=1, undo=True, maxundo=-1,
            padx=8, pady=2)
        self.t.pack(expand=True, fill=tk.BOTH)
        self.parent.configure(background=self.settings['bar_color'])

        self.open_file()

        # So I can edit the python file indirectly
        self.parent.overrideredirect(self.settings['ORR'])
        # Could probably put this line in save but I really don't want to as it would be ignored 99.999% of the time

        # An autosave feature.
        # q exists cause binding returns unnecessary data, just like how q is an unnecessary letter; needs to be put *somewhere*
        self.t.bind('<KeyRelease>', lambda q: self.save())
        # t.focus_set(), for focusing on this widget on startup

        # Whenever you click the X button, automatically saves before closing itself
        self.parent.protocol('WM_DELETE_WINDOW', lambda: [self.save(), root.destroy()])


    def open_file(self):
        # our ram file is always our most current file
        with open(self.ram_file, 'r') as ram:
            self.t.insert(tk.INSERT, ram.read()[:-1])  # -1 is to omit the extra line the program adds
    

    # these files have to be opened at different times, which is why they are separated by function call

    def open_settings(self):
        with open(self.config_file, 'r') as config:
            self.geo = config.read().strip()

        with open(self.imm_config_file, 'r') as immc:
            self.settings = {}

            for row in immc:
                if row[0] not in ['#', '\n']:
                    x = row.split()
                    self.settings[x[0][:-1]] = x[1]


    def save(self):
        for file in self.backups_list:
            with open(file, 'w') as f:
                f.write(self.t.get('1.0', tk.END))

        with open(self.config_file, 'w') as config:
            config.write(
                '{}x{}'.format(str(root.winfo_width()), str(root.winfo_height()))
                +
                '+{}+{}'.format(str(root.winfo_rootx() + int(self.settings['rootx_adjust'])),
                                str(root.winfo_rooty() + int(self.settings['rooty_adjust'])))
            )


if __name__ == "__main__":
    root = tk.Tk()

    StickyNoteWidget(root)

    root.mainloop()
