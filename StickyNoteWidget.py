import tkinter as tk
from os import environ
from datetime import datetime as date


class StickyNoteWidget:
    def __init__(self, parent):

        self.parent = parent
        self.settings = {}

        # make title empty (default is "tk")
        self.parent.title('')

        # extract StickyNoteWidget directory from Environment Variables. Use this template to pinpoint the directory of every file.
        directoryTemplate = environ['StickyNoteWidgetData'] + 'textFiles/1/{}'

        # date.today().isoweekday() will return today's day of the week as an integer. Monday is 1, Tuesday is 2...
        self.backupToday = directoryTemplate.format('backup' + str(date.today().isoweekday()) + '.txt')

        self.ramFile = directoryTemplate.format('ram.txt')
        self.configFile = directoryTemplate.format('config.txt')
        self.immConfigFile = directoryTemplate.format('immutableConfig.txt')

        # includes all settings: dimensions, location, fontSize, etc.
        self.readSettings()

        # set window's dimensions and location
        self.parent.geometry(self.settings['geo'])

        # a frame with no widgets attached. Provides the extra bar under the titlebar.
        aestheticFrame = tk.Frame(root)  
        aestheticFrame.pack(pady=11)

        # set the color of aestheticFrame
        self.parent.configure(background=self.settings['barColor'])
        
        # create Text widget
        self.textBox = tk.Text(root,
            bg=self.settings['bgColor'], 
            fg=self.settings['fontColor'],
            font=(self.settings['fontFamily'], 
            int(self.settings['fontSize']), 
            self.settings['fontWeight'].lower()),
            insertbackground=self.settings['fontColor'], 
            insertborderwidth=1, 
            undo=True, 
            maxundo=-1,
            padx=8, pady=2
        )

        self.textBox.pack(expand=True, fill=tk.BOTH)

        self.readTextData()

        # `ORR == True`` will result in no Windows title bar. This perhaps has better aesthetic but makes the window impossible to move and difficult to close (requires the use of "End Task" in Task Manager).
        self.parent.overrideredirect(self.settings['ORR'])

        # Autosave constantly. `q` is a filler variable; never used.
        self.textBox.bind('<KeyRelease>', lambda q: self.saveData())

        # Upon user clicking `X`, save the file before closing the window
        self.parent.protocol('WM_DELETE_WINDOW', lambda: [self.saveData(), root.destroy()])


    def readTextData(self):
        with open(self.ramFile, 'r') as ram:
            self.textBox.insert(tk.INSERT, ram.read()[:-1])
            # -1 is to omit the extra line the program adds


    def readSettings(self):
        with open(self.configFile, 'r') as config:
            self.settings["geo"] = config.read().strip()

        with open(self.immConfigFile, 'r') as immc:
            for row in immc:
                if row[0] not in ['#', '\n']:
                    x = row.split()
                    self.settings[x[0][:-1]] = x[1]


    def saveData(self):
        for file in [self.backupToday, self.ramFile]:
            with open(file, 'w') as f:
                f.write(self.textBox.get('1.0', tk.END))

        # save dimensions and location in a specific format (`315x330+467+388`) so as to be easily reused as an argument in self.parent.geometry() upon reopening StickyNoteWidget
        # xAdjust and yAdjust circumvent geometry glitches
        with open(self.configFile, 'w') as config:
            config.write(
                '{}x{}+{}+{}'.format(
                    str(root.winfo_width()), 
                    str(root.winfo_height()),
                    str(root.winfo_rootx() 
                    + int(self.settings['xAdjust'])),
                    str(root.winfo_rooty() 
                    + int(self.settings['yAdjust']))
                )
            )


if __name__ == "__main__":
    root = tk.Tk()

    StickyNoteWidget(root)

    root.mainloop()
