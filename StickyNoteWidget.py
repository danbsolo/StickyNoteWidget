import tkinter as tk
from os import path, makedirs
from datetime import datetime as date


class StickyNoteWidget:
    def __init__(self, parentWindow, title):

        self.parentWindow = parentWindow
        self.settings = {}

        self.parentWindow.title(title)

        # absolute path of StickyNoteWidget.py + "/StickyNotes/" + title
        # Use this template to pinpoint the directory of every file.
        parentDir = path.dirname(path.abspath(__file__)) + "/StickyNotes/" + title

        # date.today().isoweekday() will return today's day of the week as an integer. Monday is 1, Tuesday is 2...
        self.backupToday = parentDir + '/backup' + str(date.today().isoweekday()) + '.txt'

        self.ramFile = parentDir + '/ram.txt'
        self.configFile = parentDir + '/config.txt'
        self.immConfigFile = parentDir + '/immutableConfig.txt'

        # if this specific StickyNote does not yet exist, create it. If the StickyNotes subfolder happens to not exist either, create that as well
        if not path.exists(parentDir):
            makedirs(parentDir)

        # if the ram file doesn't exist, create it
        if not path.exists(self.ramFile):
            with open(self.ramFile, 'w') as ramF:
                ramF.write("Type here!")

        # if either config or immConfig doesn't exist, reset both
        if not (path.exists(self.configFile) and path.exists(self.immConfigFile)):
            with open(self.immConfigFile, 'w') as immConfigF:
                immConfigF.write("# Settings\n\nbgColor: #093553\nbarColor: #2980B9\n\nfontColor: White\nfontFamily: Consolas\nfontSize: 12\nfontWeight: normal\n\n\n# set these to 0 if adjusting the window's spawn location isn't necessary\nxAdjust: -8\nyAdjust: -31\n\n# if unsure, leave at false\nORR: false")

            with open(self.configFile, 'w') as configF:
                configF.write("300x200+100+100")
        

        # includes all settings: dimensions, location, fontSize, etc.
        self.readSettings()

        # set window's dimensions and location
        self.parentWindow.geometry(self.settings['geometry'])

        # a frame with no widgets attached. Provides the extra bar under the titlebar.
        aestheticFrame = tk.Frame(parentWindow)  
        aestheticFrame.pack(pady=11)

        # set the color of aestheticFrame
        self.parentWindow.configure(background=self.settings['barColor'])
        
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

        # `ORR == True` will result in no Windows title bar. This perhaps has better aesthetic but makes the window impossible to move and difficult to close (requires the use of "End Task" in Task Manager).
        self.parentWindow.overrideredirect(self.settings['ORR'])

        # Autosave constantly. `q` is a required filler variable; never used.
        self.textBox.bind('<KeyRelease>', lambda q: self.saveData())

        # Upon user clicking `X`, save the file before closing the window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: [self.saveData(), root.destroy()])


    def readTextData(self):
        with open(self.ramFile, 'r') as ramF:
            self.textBox.insert(tk.INSERT, ramF.read())
            # -1 is to omit the extra line the program adds


    def readSettings(self):
        with open(self.configFile, 'r') as configF:
            self.settings["geometry"] = configF.read().strip()

        with open(self.immConfigFile, 'r') as immConfigF:
            for row in immConfigF:
                if row[0] not in ['#', '\n']:
                    x = row.split()
                    self.settings[x[0][:-1]] = x[1]


    def saveData(self):
        for file in [self.backupToday, self.ramFile]:
            with open(file, 'w') as f:
                f.write(self.textBox.get('1.0', 'end-1c'))

        # save dimensions and location in a specific format (`315x330+467+388`) so as to be easily reused as an argument in self.parent.geometry() upon reopening StickyNoteWidget
        # xAdjust and yAdjust circumvent geometry glitches
        with open(self.configFile, 'w') as configF:
            configF.write(
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

    StickyNoteWidget(root, "mainSticky")

    root.mainloop()
