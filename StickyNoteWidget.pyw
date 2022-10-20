import tkinter as tk
from tkinter import font
from os import path, mkdir, makedirs, scandir, path, remove
from datetime import datetime as date
import sqlite3 as sql


class StickyNoteWidget:
    def __init__(self, parentWindow, title, stickyNoteHub):
        
        self.title = title
        self.hub = stickyNoteHub
        self.parentWindow = parentWindow
        self.settings = {}

        self.parentWindow.title(self.title)

        self.readSettings()
        
        self.setGeometry()


        self.parentWindow.configure(background=self.settings['BarColor'])
        aestheticBar = tk.Label(parentWindow, bg=self.settings['BarColor'])
        aestheticBar.pack()

        # Set up textBox's font using the font class for easy mutability
        self.settings['FontSize'] = int(self.settings['FontSize'])

        self.textBoxFont = font.Font(
            family=self.settings['FontFamily'],
            size=self.settings['FontSize']
        )
        
        # create Text widget
        self.textBox = tk.Text(self.parentWindow,
            bg=self.settings['BgColor'], 
            fg=self.settings['FontColor'],
            font=self.textBoxFont,
            insertbackground=self.settings['FontColor'],
            bd=0,
            padx=8, pady=2, # spaces text away from the window's border a bit
            undo=True, 
            maxundo=-1,
            wrap=tk.WORD
        )

        # if user changes window size, textBox is to expand to fill it
        self.textBox.pack(expand=tk.TRUE, fill=tk.BOTH)
        
        self.insertRawText()

        self.saveRawTextData()


        # update parentWindow early, allowing recursive savePositionData() function to work properly
        self.parentWindow.update()
        self.savePositionData()


        # save window dimensions
        self.textBox.bind('<Configure>', lambda q: self.saveDimensionData())

        
        # Autosave while typing. `q` is a required filler variable; never used.
        self.textBox.bind('<KeyRelease>', lambda q: self.saveRawTextData())

        # ctrl+plus/equal and ctrl+minus to increase and decrease fontSize by 1 respectively
        self.textBox.bind('<Control-plus>', lambda q: self.changeFontSize(1))
        self.textBox.bind('<Control-equal>', lambda q: self.changeFontSize(1))
        self.textBox.bind('<Control-minus>', lambda q: self.changeFontSize(-1))

        # close the current Sticky Note
        self.textBox.bind('<Control-w>', lambda q: self.closeWindow())

        # save the current Sticky Note. Autosave covers most actions regardless
        self.textBox.bind('<Control-s>', 
        lambda q: [self.saveRawTextData(), 
        self.parentWindow.title("SAVED " + self.title),
        self.parentWindow.after(1000, lambda: self.parentWindow.title(self.title))
        ])

        # Upon user clicking `X`, save the file before closing the window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: [self.closeWindow()])


    def insertRawText(self):
        self.textBox.insert(tk.INSERT, self.settings['RawText'])


    def setGeometry(self):
        self.parentWindow.geometry(
            "{}x{}+{}+{}".format(
                self.settings['DimensionX'],
                self.settings['DimensionY'],
                self.settings['PositionX'],
                self.settings['PositionY']
            )
        )


    def changeFontSize(self, increment):
        
        # minimum 8 and maximum 50 fontSize
        if (self.settings['FontSize'] <= 8 and increment < 0) or \
            (self.settings['FontSize'] >= 50 and increment > 0):
            return

        self.settings['FontSize'] += increment
        self.textBoxFont.config(size = self.settings['FontSize'])

        self.hub.db.execute("\
            UPDATE STICKYNOTE\
            SET FontSize == ?\
            WHERE Title == ?", (
                self.settings['FontSize'],
                self.title
            ))
        
        
    def readSettings(self):        
        self.hub.db.execute("\
            SELECT *\
            FROM STICKYNOTE\
            WHERE Title == \"{}\"".format(self.title))

        self.settings = dict(self.hub.db.fetchone())


    def saveRawTextData(self):        
        self.hub.db.execute("UPDATE STICKYNOTE\
            SET RawText == ?\
            WHERE Title == ?", (
                self.textBox.get('1.0', 'end-1c'),
                self.title
            ))

        self.hub.connector.commit()


    def saveDimensionData(self):
        self.hub.db.execute("\
            UPDATE STICKYNOTE\
            SET DimensionX == ?,\
            DimensionY == ?\
            WHERE Title == ?", (
                self.parentWindow.winfo_width(),
                self.parentWindow.winfo_height(),
                self.title))


        self.hub.connector.commit()


    def savePositionData(self):
        self.hub.db.execute("UPDATE STICKYNOTE\
            SET PositionX == ?,\
            PositionY == ?\
            WHERE Title = ?", (
                self.parentWindow.winfo_rootx() + 
                self.hub.adjustPositions['AdjustPositionX'],
                self.parentWindow.winfo_rooty() +
                self.hub.adjustPositions['AdjustPositionY'],
                self.title
            ))

        # 10000 miliseconds = 10 seconds
        self.parentWindow.after(10000, self.savePositionData)
        self.hub.connector.commit()


    def closeWindow(self):
        self.saveRawTextData()

        self.parentWindow.destroy()

        self.hub.removeStickyNote(self)
    

    def __repr__(self):
        return self.title

        

class StickyNoteHub:
    def __init__(self, parentWindow):
        
        self.parentWindow = parentWindow
        self.parentWindow.title("StickyNoteHub")
        self.parentWindow.geometry("250x100")

        # minimize the window using the "iconify()" method
        self.parentWindow.iconify()


        self.parentDir = path.dirname(path.abspath(__file__))
        self.databaseDir = self.parentDir + '/stickyNoteWidget.db'


        if path.exists(self.databaseDir):
            self.firstOpen = False
        else:
            self.firstOpen = True

        self.connector = sql.connect(self.databaseDir)
        self.connector.row_factory = sql.Row
        self.db = self.connector.cursor()

        if self.firstOpen:
            self.createTables()

        
        # extract AdjustPositionX/Y data
        if self.firstOpen:
            self.db.execute("\
                INSERT INTO ADVANCEDCONFIG\
                VALUES (?, ?)",
                (-8, -31))

        self.db.execute("\
            SELECT AdjustPositionX, AdjustPositionY\
            FROM ADVANCEDCONFIG\
            ")
        
        self.adjustPositions = dict(self.db.fetchone())


        # open all StickyNotes
        self.allStickyNotes = []
        self.openedStickyNotes = []

        # default stickyNote
        if self.firstOpen:
            self.db.execute(
                "INSERT INTO StickyNote\
                (Title, RawText, DimensionX, DimensionY, PositionX, PositionY, BgColor, BarColor, FontColor, FontFamily, FontSize) \
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("mainSticky", "mainSticky", 300, 200, 100, 100, "#093553", "#2980B9", "#FFFFFF", "Consolas", 12))


        self.db.execute("\
            SELECT * FROM STICKYNOTE\
                ")

        self.allStickyNotes = self.db.fetchall()


        for stickyNote in self.allStickyNotes:
            stickyNote = dict(stickyNote)
            
            self.openedStickyNotes.append(StickyNoteWidget(
                tk.Toplevel(), stickyNote['Title'], self))


        # create a label in the root window, then update text accordingly
        self.openedStickyNoteLabel = tk.Label(self.parentWindow)
        self.updateOpenedStickyNoteLabel()
        self.openedStickyNoteLabel.pack()

        # Upon user clicking `X`, save the file before closing the window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: [self.closeProgram()])


    def removeStickyNote(self, stickyNote: StickyNoteWidget):
        
        # close window and remove this StickyNote from list of opened StickyNotes
        self.openedStickyNotes.remove(stickyNote)

        self.updateOpenedStickyNoteLabel()

        # if no StickyNoteWidgets are open anymore, close the whole program
        if self.openedStickyNotes == []:
            self.closeProgram()
    

    def updateOpenedStickyNoteLabel(self):
        totalString = ""

        for stickyNote in self.openedStickyNotes:
            totalString += stickyNote.title + "\n"

        # do "[:-1]" of totalString to exclude the final newline character ("\n")
        self.openedStickyNoteLabel.config(text=totalString[:-1])

    
    def closeProgram(self):
        for stickyNote in self.openedStickyNotes:
            stickyNote.saveRawTextData()
        
        self.db.close()
        self.connector.close()

        self.parentWindow.destroy()


    def createTables(self):
        self.db.execute("\
            CREATE TABLE STICKYNOTE(\
            ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            Title TEXT UNIQUE,\
            RawText TEXT,\
            DimensionX INT,\
            DimensionY INT,\
            PositionX INT,\
            PositionY INT,\
            BgColor VARCHAR(7),\
            BarColor VARCHAR(7),\
            FontColor VARCHAR(7),\
            FontFamily TEXT,\
            FontSize INT\
            )")


        self.db.execute("\
            CREATE TABLE ADVANCEDCONFIG(\
            AdjustPositionX INT,\
            AdjustPositionY INT\
            )")




if __name__ == "__main__":
    root = tk.Tk()

    StickyNoteHub(root)

    root.mainloop()
