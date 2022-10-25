import tkinter as tk
from tkinter import font
from os import path
import sqlite3 as sqlite
from tkinter import simpledialog
from tkinter import messagebox


class StickyNoteWidget:
    def __init__(self, parentWindow, title, stickyNoteHub):

        self.hub = stickyNoteHub
        self.parentWindow = parentWindow
        
        self.title = title
        self.parentWindow.title(self.title)

        if path.exists(self.hub.parentDir + '/icons/bwStickyNote.ico'):
            self.parentWindow.iconbitmap(self.hub.parentDir + '/icons/bwStickyNote.ico')

        self.settings = {}
        self.readSettings()
        self.setGeometry()

        # set color of the aestheticBar (directly below the titleBar)
        self.parentWindow.configure(background=self.settings['BarColor'])
        aestheticBar = tk.Label(parentWindow, bg=self.settings['BarColor'])
        aestheticBar.pack()


        # set up textBox's font using the font class for easy mutability
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

        # if user resizes window, textBox is to expand to fill it
        self.textBox.pack(expand=tk.TRUE, fill=tk.BOTH)
        
        self.insertRawText()


        # automatically save all relevant data when stickyNote loses focus
        self.parentWindow.bind('<FocusOut>', lambda q: self.saveData())

        # ctrl+plus/equal and ctrl+minus to increase and decrease fontSize respectively
        self.parentWindow.bind('<Control-plus>', lambda q: self.changeFontSize(1))
        self.parentWindow.bind('<Control-equal>', lambda q: self.changeFontSize(1))
        self.parentWindow.bind('<Control-minus>', lambda q: self.changeFontSize(-1))

        # close (and save) the current stickyNote
        self.parentWindow.bind('<Control-w>', lambda q: self.closeWindow())

        # upon user clicking `X`, save data before closing the window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: self.closeWindow())
        

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
        """Minimum of 8. Maximum of 50."""
        
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
            WHERE Title == \"{}\"".format(
                self.title))

        self.settings = dict(self.hub.db.fetchone())


    def saveData(self):
        print("SAVING", self.title)
        self.hub.db.execute("\
            UPDATE STICKYNOTE\
            SET RawText == ?,\
            DimensionX == ?,\
            DimensionY == ?,\
            PositionX == ?,\
            PositionY == ?\
            WHERE TITLE == ?", (
                self.textBox.get('1.0', 'end-1c'),
                self.parentWindow.winfo_width(),
                self.parentWindow.winfo_height(),
                self.parentWindow.winfo_rootx() + 
                self.hub.adjustPositions['AdjustPositionX'],
                self.parentWindow.winfo_rooty() +
                self.hub.adjustPositions['AdjustPositionY'],
                self.title
            ))

        self.hub.connector.commit()


    def closeWindow(self):
        self.saveData()

        self.parentWindow.withdraw()

        self.hub.removeStickyNoteObject(self)
    

    def __repr__(self):
        return self.title

        

class StickyNoteHub:
    def __init__(self, parentWindow):

        self.parentWindow = parentWindow
        self.parentWindow.title("StickyNoteHub")


        self.parentWindow.resizable(0, 0)

        # minimize the window; iconify it
        self.parentWindow.iconify()

        # extract the absolute path of the current folder
        self.parentDir = path.dirname(path.abspath(__file__))
        
        # errorHandling: check if the file exists before using it
        if path.exists(self.parentDir + '/icons/bwHub.ico'):
            self.parentWindow.iconbitmap(self.parentDir + '/icons/bwHub.ico')

        self.databaseDir = self.parentDir + '/stickyNoteWidget.db'

        # if the path exists, it's not the user's first open
        self.firstOpen = not path.exists(self.databaseDir)


        # *row_factory* facilitates converting query results into dictionaries
        self.connector = sqlite.connect(self.databaseDir)
        self.connector.row_factory = sqlite.Row
        self.db = self.connector.cursor()

        if self.firstOpen:
            self.createSQLiteTables()
        

        # extract AdjustPositionX/Y data. Makes up for TKinter's glitchy geometry setting later
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


        self.allStickyNoteObjects = []
        self.openedStickyNoteObjects = []

        # default stickyNote
        if self.firstOpen:
            self.insertDefaultStickyNote("defaultSticky")

        self.db.execute("\
            SELECT * FROM STICKYNOTE\
            ORDER BY Title")


        # open all sticky notes
        for stickyNoteData in self.db.fetchall():
            stickyNoteData = dict(stickyNoteData)

            stickyNoteObject = StickyNoteWidget(
                tk.Toplevel(), stickyNoteData['Title'], self)
            
            self.allStickyNoteObjects.append(stickyNoteObject)
            self.openedStickyNoteObjects.append(stickyNoteObject)

        self.contentFrame = None
        self.refreshHubContent()
        
        self.parentWindow.deiconify() # debug type code

        # Upon user clicking `X`, save all data before closing the window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: [self.closeProgram()])


    def updateHubContent(self, stickyNoteObject):            
            tk.Label(self.contentFrame, text=stickyNoteObject.title, width=20).grid(row=self.nextRow, column=1, padx=20, pady=5)
            
            tk.Button(
            self.contentFrame, text="TOG", 
            command=lambda: [self.toggleOpen(stickyNoteObject)],
            ).grid(row=self.nextRow, column=2, padx=5)

            tk.Button(self.contentFrame, text="DEL", 
            command=lambda: self.deleteStickyNote(stickyNoteObject)
            ).grid(row=self.nextRow, column=3, padx=5)

            self.nextRow += 1


    def toggleOpen(self, stickyNoteObject):
        if stickyNoteObject.parentWindow.winfo_viewable():
            stickyNoteObject.closeWindow()

        else:
            self.openedStickyNoteObjects.append(stickyNoteObject)
            stickyNoteObject.parentWindow.deiconify()


    def refreshHubContent(self):
        if self.contentFrame:
            self.contentFrame.destroy()
        
        self.contentFrame = tk.Frame(self.parentWindow)
        self.contentFrame.grid()

        self.nextRow = 0

        self.addButton = tk.Button(
            self.contentFrame, text="+", command=self.queryNewStickyNote)
        self.addButton.grid(row=self.nextRow, column=3)

        self.nextRow += 1

        for stickyNoteObject in self.allStickyNoteObjects:
            self.updateHubContent(stickyNoteObject)
    

    def deleteStickyNote(self, stickyNoteObject):
        confirmation = messagebox.askyesno(
            "Are you sure?", "{} is to be deleted. This is an irreversible action.".format(stickyNoteObject.title))
        
        if not confirmation:
            return

        self.removeStickyNoteObject(stickyNoteObject)
        self.allStickyNoteObjects.remove(stickyNoteObject)
        
        self.refreshHubContent()

        self.db.execute("\
            DELETE FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                stickyNoteObject.title))
        
        self.connector.commit()


    def insertDefaultStickyNote(self, title):
            self.db.execute(
                "INSERT INTO StickyNote\
                (Title, RawText, DimensionX, DimensionY, PositionX, PositionY, BgColor, BarColor, FontColor, FontFamily, FontSize) \
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, title, 300, 200, 400, 400, "#093553", "#2980B9", "#FFFFFF", "Consolas", 12))


    def queryNewStickyNote(self):
        newTitle = simpledialog.askstring("Add New stickyNote", "Enter new title~")

        if newTitle.strip() == "":
            return
        elif len(newTitle) >= 21:
            messagebox.showerror("TypeError", "Max character length of 20!")
            return

        if '\"' in newTitle or "\'" in newTitle:
            messagebox.showerror("TypeError", "No quotation marks!")
            return
    
        try:
            self.insertDefaultStickyNote(newTitle)
        except sqlite.IntegrityError:
            messagebox.showerror("IntegrityError", "{} is already in use!".format(newTitle))
            return

        self.db.execute("\
            SELECT * FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                newTitle
            ))
        
        newStickyNote = dict(self.db.fetchone())

        newStickyNoteObject = StickyNoteWidget(
            tk.Toplevel(), newStickyNote['Title'], self)

        self.allStickyNoteObjects.append(newStickyNoteObject)
        self.openedStickyNoteObjects.append(newStickyNoteObject)

        self.updateHubContent(newStickyNoteObject)
        

    def removeStickyNoteObject(self, stickyNoteObject):
        
        # remove this stickyNoteObject from list
        self.openedStickyNoteObjects.remove(stickyNoteObject)

        # if no stickyNotes are open anymore, close the whole program
        if self.openedStickyNoteObjects == []:
            self.closeProgram()
    
    
    def closeProgram(self):
        for stickyNote in self.openedStickyNoteObjects:
            stickyNote.saveData()
        
        self.db.close()
        self.connector.close()

        self.parentWindow.destroy()


    def createSQLiteTables(self):
        self.db.execute("\
            CREATE TABLE STICKYNOTE(\
            ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            Title TEXT UNIQUE COLLATE NOCASE NOT NULL,\
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