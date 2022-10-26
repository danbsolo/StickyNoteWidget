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

        self.hub.removeStickyNote(self)
    

    def __repr__(self):
        return self.title

        

class StickyNoteHub:
    def __init__(self, parentWindow):

        self.parentWindow = parentWindow
        self.parentWindow.title("StickyNoteHub")
        self.parentWindow.resizable(0, 0)

        # minimize the window; iconify it: self.parentWindow.iconify()

        # extract the absolute path of the current folder
        self.parentDir = path.dirname(path.abspath(__file__))
        
        # errorHandling: check if the image file exists before using it
        if path.exists(self.parentDir + '/icons/bwHub.ico'):
            self.parentWindow.iconbitmap(self.parentDir + '/icons/bwHub.ico')

        self.databaseDir = self.parentDir + '/stickyNoteWidget.db'

        # if the path exists, it's not the user's first open. And vice versa.
        self.firstOpen = not path.exists(self.databaseDir)


        # *row_factory* facilitates casting query results as dictionaries
        self.connector = sqlite.connect(self.databaseDir)
        self.connector.row_factory = sqlite.Row
        self.db = self.connector.cursor()


        # extract AdjustPositionX/Y data. Makes up for TKinter's glitchy geometry setting later
        if self.firstOpen:
            self.createSQLiteTables()

            self.insertDefaultStickyNote("defaultSticky")

            self.db.execute("\
                INSERT INTO ADVANCEDCONFIG\
                VALUES (?, ?)",
                (-8, -31))


        self.db.execute("\
            SELECT AdjustPositionX, AdjustPositionY\
            FROM ADVANCEDCONFIG\
            ")
        
        self.adjustPositions = dict(self.db.fetchone())


        # keep track of all stickyNotes, along with which are opened.
        self.allStickyNotes = []
        self.openedStickyNotes = []

        self.db.execute("\
            SELECT Title FROM STICKYNOTE\
            ORDER BY Title")
        
        for stickyNoteData in self.db.fetchall():
            stickyNoteData = dict(stickyNoteData)

            stickyNoteObject = StickyNoteWidget(
                tk.Toplevel(), stickyNoteData['Title'], self)
            
            self.allStickyNotes.append(stickyNoteObject)
            self.openedStickyNotes.append(stickyNoteObject)


        self.contentFrame = None
        self.contentFrameBG = "#202124" # near dark gray
        self.defaultBG = "#F0F0F0"
        self.darkerDefaultBG = "#B0B0B0"

        self.refreshHubContent()


        # Upon user clicking `X`, save all data before closing the window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: [self.closeApplication()])


    def updateHubContent(self, stickyNote):  
            """Each stickyNote, opened or not, is represented by one row in StickyNoteHub."""

            # Hacky workaround; an extra frame is required in order to give titleWidget a colored border
            titleWidgetFrame = tk.Frame(
                self.contentFrame,
                bg=self.contentFrameBG,
                highlightbackground=stickyNote.settings['BarColor'],
                highlightthickness=4)
            titleWidgetFrame.grid(row=self.currentRow, column=0, 
                padx=11, pady=3)

            titleWidget = tk.Label(
                titleWidgetFrame, text=stickyNote.title, width=22,
                bg=stickyNote.settings['BgColor'],
                fg=stickyNote.settings['FontColor'],
                font=(stickyNote.settings['FontFamily'], 12)
                )
            titleWidget.grid(row=self.currentRow, column=0)
            

            toggleWidget = tk.Button(
                self.contentFrame, text="MIN/MAX", 
                command=lambda: [self.toggleOpen(stickyNote)],
                )
            toggleWidget.grid(row=self.currentRow, column=1, padx=5)

            self.setHoverBackgroundBindings(
                    toggleWidget, self.darkerDefaultBG, self.defaultBG)


            deleteWidget = tk.Button(
                self.contentFrame, text="DEL", 
                command=lambda: self.deleteStickyNote(stickyNote),
                bg="#FF6666"
                )
            deleteWidget.grid(row=self.currentRow, column=2, padx=5)

            self.setHoverBackgroundBindings(
                deleteWidget, "#FF2222", "#FF9999")


            self.currentRow += 1


    def toggleOpen(self, stickyNoteObject):
        """Toggle "open" state of the stickyNote. Note that the closeWindow method removes stickyNotes from openedStickyNotes regardless."""
        
        if stickyNoteObject.parentWindow.winfo_viewable():
            stickyNoteObject.closeWindow()
        else:
            self.openedStickyNotes.append(stickyNoteObject)
            stickyNoteObject.parentWindow.deiconify()


    def refreshHubContent(self):
        """Used to refresh hub's entire display. Used on startup or when deleting a stickyNote."""

        # reset the frame
        if self.contentFrame:
            self.contentFrame.destroy()
        
        self.contentFrame = tk.Frame(
            self.parentWindow,
            bg=self.contentFrameBG)
        self.contentFrame.grid()

        # add header widgets
        self.currentRow = 0

        self.hubLabel = tk.Label(
            self.contentFrame, text="StickyNoteHub",
            bg=self.contentFrameBG,
            fg="#FFFFFF",
            font=("Segoe UI", 20, "italic")
        )
        self.hubLabel.grid(row=self.currentRow, column=0, columnspan=2)

        self.newStickyNoteButton = tk.Button(
            self.contentFrame, text=" + ", 
            command=self.queryNewStickyNote,
            font=15,
            bg="light green"
            )
        self.newStickyNoteButton.grid(row=self.currentRow, column=2, 
            pady=10, padx=5)
            
        self.setHoverBackgroundBindings(
            self.newStickyNoteButton, "#00CC00", "light green")

        self.currentRow += 1


        # re-add every stickyNote into the reset frame
        for stickyNote in self.allStickyNotes:
            self.updateHubContent(stickyNote)


    def setHoverBackgroundBindings(self, widget, enterColor, leaveColor):
        widget.bind('<Enter>', 
            lambda q: widget.config(bg=enterColor))

        widget.bind('<Leave>', 
            lambda q: widget.config(bg=leaveColor))
    

    def deleteStickyNote(self, stickyNote):
        confirmation = messagebox.askyesno(
            "Are you sure?", "{} is to be deleted. This is an irreversible action.".format(
                stickyNote.title))
        
        if not confirmation:
            return

        # stickyNote.closeWindow() only withdraws a window. In this case, we want it destroyed completely.

        self.db.execute("\
            DELETE FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                stickyNote.title))
        
        self.connector.commit()
        
        # if the application's already closed, no need to execute any further.
        if self.removeStickyNote(stickyNote):
            return
        
        self.allStickyNotes.remove(stickyNote)
        stickyNote.parentWindow.destroy()
        
        self.refreshHubContent()


    def insertDefaultStickyNote(self, title):
            """Called on firstOpen or when creating a new stickyNote."""

            self.db.execute(
                "INSERT INTO StickyNote\
                (Title, RawText, DimensionX, DimensionY, PositionX, PositionY, BgColor, BarColor, FontColor, FontFamily, FontSize) \
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (title, title, 300, 200, 400, 400, "#093553", "#2980B9", "#FFFFFF", "Segoe UI", 12))


    def queryNewStickyNote(self):
        newTitle = simpledialog.askstring(
            "Add New stickyNote", "Enter new title~")

        # errorHandle several situations
        if not newTitle:
            return
        elif newTitle.strip() == "":
            return
        elif len(newTitle) > 20:
            messagebox.showerror("TypeError", "Max character length of 20!")
            return
        elif '\"' in newTitle or "\'" in newTitle:
            messagebox.showerror("TypeError", "No quotation marks!")
            return
    
        try:
            self.insertDefaultStickyNote(newTitle)
        except sqlite.IntegrityError:
            messagebox.showerror(
                "IntegrityError", 
                "{} is already in use!".format(
                    newTitle))
            return


        self.db.execute("\
            SELECT * FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                newTitle
            ))
        
        newStickyNoteData = dict(self.db.fetchone())

        newStickyNote = StickyNoteWidget(
            tk.Toplevel(), newStickyNoteData['Title'], self)

        self.allStickyNotes.append(newStickyNote)
        self.openedStickyNotes.append(newStickyNote)

        self.updateHubContent(newStickyNote)
        

    def removeStickyNote(self, stickyNote):
        """Remove stickyNote from openedStickNotes. Close the application if no stickyNotes are open anymore.

        Return True if application has indeed been closed. Otherwise, False."""
        
        self.openedStickyNotes.remove(stickyNote)

        # if no stickyNotes are open anymore, close the whole application
        if self.openedStickyNotes == []:
            self.closeApplication()
            return True
        
        return False
    
    
    def closeApplication(self):
        """Because StickyNoteHub is the "root" window to all of the Toplevel widgets (the actual stickyNotes), closing it will close everything else automatically."""

        for stickyNote in self.openedStickyNotes:
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