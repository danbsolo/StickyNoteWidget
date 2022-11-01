import tkinter as tk
from tkinter import font
from os import path
import sqlite3 as sqlite
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import colorchooser
from sys import modules as importedModules

# enable user to run StickyNoteWidget.pyw without PIL
try:
    from PIL import Image, ImageTk
except ModuleNotFoundError:
    pass


class StickyNoteWidget:
    def __init__(self, parentWindow, title, stickyNoteHub):
        # Each stickyNote has several buttons instantiated by StickyNoteHub. They are: 
        # titleLabelFrame, titleLable, toggleButton, backgroundColorButton, barColorButton, fontColorButton, fontFamilyButton, deleteButton

        self.hub = stickyNoteHub
        self.parentWindow = parentWindow
        
        self.title = title
        self.parentWindow.title(self.title)

        # errorHandling: check if the image file exists before using it. Running theme in this program.
        if path.exists(self.hub.parentDir + '/icons/bwStickyNote.ico'):
            self.parentWindow.iconbitmap(self.hub.parentDir + '/icons/bwStickyNote.ico')

        self.readSettings()
        self.setGeometry()


        # set color of the aestheticBar (located directly below the titleBar)
        self.parentWindow.config(bg=self.settings['BarColor'])
        self.aestheticBar = tk.Label(
            parentWindow, bg=self.settings['BarColor'])
        self.aestheticBar.pack()


        # set up textBox's font using the font class for easy mutability
        self.textBoxFont = font.Font(
            family=self.settings['FontFamily'],
            size=self.settings['FontSize']
        )
        
        # create designated Text widget
        self.textBox = tk.Text(self.parentWindow,
            bg=self.settings['BackgroundColor'], 
            fg=self.settings['FontColor'],
            font=self.textBoxFont,
            insertbackground=self.settings['FontColor'],
            bd=0,
            padx=8, pady=2,
            undo=True, 
            maxundo=-1,
            wrap=tk.WORD
        )

        # if user resizes window, textBox is to expand to fill it
        self.textBox.pack(expand=tk.TRUE, fill=tk.BOTH)
        
        self.textBox.insert(tk.INSERT, self.settings['RawText'])



        # set up stickyNote's rightClickMenu
        self.changeColorMenu = tk.Menu(self.parentWindow, tearoff=False)

        self.changeColorMenu.add_command(
            label="Background", command=
            lambda: self.hub.changeColor(self, "BackgroundColor"))
        self.changeColorMenu.add_command(
            label="Bar", command=
            lambda: self.hub.changeColor(self, "BarColor"))
        self.changeColorMenu.add_command(
            label="Font", command=
            lambda: self.hub.changeColor(self, "FontColor"))
            

        self.rightClickMenu = tk.Menu(self.parentWindow, tearoff=False)

        self.rightClickMenu.add_command(
            label="Toggle StickyNoteHub", 
            command=lambda: self.hub.toggleHubWindow())

        self.rightClickMenu.add_separator()

        self.rightClickMenu.add_cascade(
            label="Change Color", menu=self.changeColorMenu)

        self.rightClickMenu.add_command(
            label="Change Font Family", 
            command=lambda: self.hub.changeFontFamily(self))

        self.rightClickMenu.add_command(
            label="Change Title", 
            command=lambda: self.hub.changeTitle(self))

        self.rightClickMenu.add_separator()

        self.rightClickMenu.add_command(
            label="Create stickyNote", 
            command=lambda: self.hub.createNewStickyNote())
        
        self.rightClickMenu.add_command(
            label="Delete stickyNote", 
            command=lambda: self.hub.deleteStickyNote(self))


        self.parentWindow.bind(
            "<Button-3>", lambda event: self.rightClickPopup(event))


        # automatically save all relevant data when stickyNote loses focus
        # when window is minimized, "de-minimize" it back to normal
        self.parentWindow.bind('<FocusOut>', lambda e: [
            self.saveData(), self.disableMinimize()
            ]
        )

        # ctrl+plus/equal and ctrl+minus to increase and decrease fontSize respectively
        self.parentWindow.bind(
            '<Control-plus>', lambda e: self.changeFontSize(1))
        self.parentWindow.bind(
            '<Control-equal>', lambda e: self.changeFontSize(1))
        self.parentWindow.bind(
            '<Control-minus>', lambda e: self.changeFontSize(-1))

        # close (and save) the current stickyNote
        self.parentWindow.bind('<Control-w>', lambda e: self.closeWindow())

        # upon user clicking `X`, change some things, then withdraw window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: self.closeWindow())



    def rightClickPopup(self, event):
        # x_root and y_root are used to determine where the menu should popup. AKA, the user's mouse coordinates.

        self.rightClickMenu.tk_popup(event.x_root, event.y_root)


    def disableMinimize(self):
        # Minimizing leads to buggy behaviour in regards to saving position. 
        # An easy way to disable minimizing is to make the Toplevel widgets transient to StickyNoteHub. However, this would result in an inadvertently strange design choice where StickyNoteHub has to be viewable for any stickyNotes to be viewable as well.
        # Hence, a hacky "disableMinimize" function.

        if self.parentWindow.state() in ["iconic", "icon"]:
            self.parentWindow.deiconify()

            self.parentWindow.title("(MINIMIZE DISABLED) " + self.title)
            self.parentWindow.after(
                1000, lambda: self.parentWindow.title(self.title))


    def readSettings(self):
        """Instantiate self.settings, a dictionary denoting a stickyNote's records."""

        self.hub.db.execute("\
            SELECT *\
            FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                self.title
            )
        )

        self.settings = dict(self.hub.db.fetchone())


    def setGeometry(self):
        """Set stickyNote's geometry (that is, window width+height and position coordinates) using stickyNote's records."""

        self.parentWindow.geometry(
            "{}x{}+{}+{}".format(
                self.settings['DimensionX'],
                self.settings['DimensionY'],
                self.settings['PositionX'],
                self.settings['PositionY']
            )
        )
    

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
            )
        )

        self.hub.connector.commit()


    def closeWindow(self):
        self.saveData()

        self.toggleButton.config(image=self.hub.toggleOffImage, text="off")

        self.parentWindow.withdraw()

        self.hub.removeFromOpenStickyNotes(self)


    def changeFontSize(self, increment):
        """Maximum FontSize of 50 and minimum of 8, as set by the CHECK constraint in the SQLite table."""
        
        try:
            self.hub.db.execute("\
                UPDATE STICKYNOTE\
                SET FontSize == ?\
                WHERE Title == ?", (
                    self.settings['FontSize'] + increment,
                    self.title
                )
            )
        except sqlite.IntegrityError:
            return

        self.settings['FontSize'] += increment
        self.textBoxFont.config(size = self.settings['FontSize'])


    def __repr__(self):
        return self.title

        

class StickyNoteHub:
    def __init__(self, parentWindow):
        self.parentWindow = parentWindow
        self.parentWindow.title("StickyNoteHub")
        self.parentWindow.resizable(0, 0)

        # extract the absolute path of the current folder
        self.parentDir = path.dirname(path.abspath(__file__))

        if path.exists(self.parentDir + '/icons/bwHub.ico'):
            self.parentWindow.iconbitmap(self.parentDir + '/icons/bwHub.ico')

        self.databaseDir = self.parentDir + '/stickyNoteWidget.db'

        # *row_factory* facilitates casting query results as dictionaries
        self.connector = sqlite.connect(self.databaseDir)
        self.connector.row_factory = sqlite.Row
        self.db = self.connector.cursor()


        # inquire if STICKYNOTE table exists
        self.db.execute("\
            SELECT * FROM sqlite_master\
            WHERE tbl_name == 'STICKYNOTE'")

        if not self.db.fetchone():
            self.createSQLiteTables()
            self.insertDefaultStickyNote("defaultSticky")
        else:
            # if STICKYNOTE table does indeed exist, inquire whether it's empty
            self.db.execute("\
                SELECT * FROM STICKYNOTE\
                LIMIT 1")
            
            if not self.db.fetchone():
                self.insertDefaultStickyNote("defaultSticky")


        # keep track of all stickyNotes, along with which are opened
        self.allStickyNotes = []
        self.openStickyNotes = []

        self.db.execute("\
            SELECT Title FROM STICKYNOTE\
            ORDER BY Title")
        
        for stickyNoteData in self.db.fetchall():
            stickyNoteData = dict(stickyNoteData)

            stickyNote = StickyNoteWidget(
                tk.Toplevel(), stickyNoteData['Title'], self)
            
            self.allStickyNotes.append(stickyNote)
            self.openStickyNotes.append(stickyNote)
        

        # AdjustPositionX/Y values may be computer dependent, hence this check on each startup
        self.adjustPositionXYvalues()
        

        self.contentFrame = None
        self.gray = "#808080"
        self.contentFrameBG = "#202124" # near dark gray
        self.defaultBG = "#F0F0F0" # Windows 10's default bg (near white)
        self.darkerDefaultBG = "#B0B0B0"



        imageFileName = [
            ['bdayPresentImage', 'birthdayPresent.ico'],
            ['garbageCanImage', 'garbageCan.ico'],
            ['toggleOffImage', 'toggleOff.ico'],
            ['toggleOnImage', 'toggleOn.ico'],
            ['mountainRangeImage', 'mountainRange.ico'],
            ['horizontalBarImage', 'horizontalBar.ico'],
            ['fontColorfulImage', 'fontColorful.ico'],
            ['fontFamilyImage', 'fontFamily.ico']
        ]
        self.prepareImages(imageFileName, (40, 40))

        self.refreshHubContent()


        # Upon user clicking `X`, save all data before closing the window
        self.parentWindow.protocol('WM_DELETE_WINDOW', lambda: [self.closeApplication()])



    
    def changeTitle(self, stickyNote):
        newTitle = self.queryNewTitle(
            "Change title", "Change title of {}~".format(
                stickyNote.settings['Title']
            )
        )

        if not newTitle:
            return

        # update actual stickyNote
        stickyNote.parentWindow.title(newTitle)

        # update database
        self.db.execute("\
            UPDATE STICKYNOTE\
            SET Title == '{}'\
            WHERE Title == '{}'".format(
                newTitle,
                stickyNote.title
            )
        )

        # update settings dictionary and title variable
        stickyNote.settings['Title'] = newTitle
        stickyNote.title = newTitle

        # update hub contents (no refresh)
        stickyNote.titleLabel.config(text=newTitle)


    def updateHubContent(self, stickyNote):  
            """Each stickyNote, open or not, is represented by one row in StickyNoteHub."""

            currentColumn = 0
            homogeneousPadx = 7
            
            # Hacky workaround; an extra frame is required in order to give titleWidget a colored border
            stickyNote.titleLabelFrame = tk.Frame(
                self.contentFrame,
                bg=self.contentFrameBG,
                highlightbackground=stickyNote.settings['BarColor'],
                highlightthickness=4)
            stickyNote.titleLabelFrame.grid(
                row=self.currentRow, column=currentColumn, 
                padx=11, pady=3)

            stickyNote.titleLabel = tk.Label(
                stickyNote.titleLabelFrame, 
                text=stickyNote.title, width=22,
                bg=stickyNote.settings['BackgroundColor'],
                fg=stickyNote.settings['FontColor'],
                font=(stickyNote.settings['FontFamily'], 12)
                )
            stickyNote.titleLabel.grid(row=self.currentRow, column=currentColumn)

            stickyNote.titleLabel.bind("<Button-1>", 
                lambda e: self.changeTitle(stickyNote))
            
            currentColumn += 1


            stickyNote.toggleButton = tk.Button(
                self.contentFrame,
                command=lambda: self.toggleStickyNoteWindow(stickyNote),
                bg=self.contentFrameBG,
                bd=0,
                activebackground=self.contentFrameBG
                )
            stickyNote.toggleButton.grid(
                row=self.currentRow, column=currentColumn,
                padx=homogeneousPadx)

            
            if stickyNote.parentWindow.winfo_viewable():
                stickyNote.toggleButton.config(
                    image=self.toggleOnImage, text="on ")
            else:
                stickyNote.toggleButton.config(
                    image=self.toggleOffImage, text="off")

            currentColumn += 1

            
            stickyNote.backgroundColorButton = tk.Button(
                self.contentFrame,
                image=self.mountainRangeImage, text="bg",
                bg=self.contentFrameBG, bd=0,
                command=lambda: self.changeColor(stickyNote, "BackgroundColor")
            )
            stickyNote.backgroundColorButton.grid(row=self.currentRow, 
            column=currentColumn, padx=homogeneousPadx)

            self.setHoverBackgroundBindings(
                    stickyNote.backgroundColorButton, self.darkerDefaultBG, self.contentFrameBG)
            
            currentColumn += 1


            stickyNote.barColorButton = tk.Button(
                self.contentFrame,
                image=self.horizontalBarImage, text="bar",
                bg=self.gray,
                bd=0,
                command=lambda: self.changeColor(stickyNote, "BarColor")
            )
            stickyNote.barColorButton.grid(row=self.currentRow, 
            column=currentColumn, padx=homogeneousPadx)

            self.setHoverBackgroundBindings(
                    stickyNote.barColorButton, self.darkerDefaultBG, self.gray)

            currentColumn += 1


            stickyNote.fontColorButton = tk.Button(
                self.contentFrame,
                image=self.fontColorfulImage, text="fg",
                bg=self.contentFrameBG, bd=0,
                command=lambda: self.changeColor(stickyNote, "FontColor")
            )
            stickyNote.fontColorButton.grid(row=self.currentRow, 
            column=currentColumn, padx=homogeneousPadx)

            self.setHoverBackgroundBindings(
                    stickyNote.fontColorButton, self.darkerDefaultBG, 
                    self.contentFrameBG)
            
            currentColumn += 1


            stickyNote.fontFamilyButton = tk.Button(
                self.contentFrame,
                image=self.fontFamilyImage, text="ff",
                bg=self.gray,
                bd=0,
                command=lambda: self.changeFontFamily(stickyNote)
            )
            stickyNote.fontFamilyButton.grid(row=self.currentRow, 
            column=currentColumn, padx=homogeneousPadx)

            self.setHoverBackgroundBindings(
                    stickyNote.fontFamilyButton, self.darkerDefaultBG, 
                    self.gray)

            currentColumn += 1


            stickyNote.deleteButton = tk.Button(
                self.contentFrame, 
                image=self.garbageCanImage, text="del", 
                command=lambda: self.deleteStickyNote(stickyNote),
                bg="#FF9999"
                )
            stickyNote.deleteButton.grid(row=self.currentRow, 
            column=currentColumn, padx=homogeneousPadx)

            self.setHoverBackgroundBindings(
                stickyNote.deleteButton, "#FF2222", "#FF9999")


            self.currentRow += 1

            # change color of buttons to accomodate lack of images
            if "PIL" not in importedModules:
                for widget in [
                stickyNote.toggleButton,
                stickyNote.backgroundColorButton,
                stickyNote.barColorButton, 
                stickyNote.fontColorButton,
                stickyNote.fontFamilyButton]:

                    widget.config(bg=self.defaultBG)
                    
                    # overwrite previous HoverBackgroundBindings
                    self.setHoverBackgroundBindings(
                        widget, self.darkerDefaultBG, self.defaultBG
                    )


    def changeFontFamily(self, stickyNote):
        newFontFamily = simpledialog.askstring(
            "Change FontFamily", "Change FontFamily from {} to~".format(
                stickyNote.settings['FontFamily']
            )
        )

        if not newFontFamily:
            return
        elif newFontFamily.strip() == '':
            return
        
        if newFontFamily.casefold() not in \
        (ff.casefold() for ff in font.families()):
            messagebox.showerror(
                "NotFoundError",
                "{} is not installed.\nReverting to {}.".format(
                    newFontFamily, stickyNote.settings['FontFamily']
                )
            )
            return
        
        # update actual stickynote
        stickyNote.textBoxFont.config(family=newFontFamily)

        # update settings dictionary
        stickyNote.settings['FontFamily'] = newFontFamily

        # update database
        self.db.execute("\
            UPDATE STICKYNOTE\
            SET {} == '{}'\
            WHERE Title == '{}'".format(
                "FontFamily",
                newFontFamily,
                stickyNote.title
                )
            )

        # update hub contents
        stickyNote.titleLabel.config(font=(newFontFamily, 12))


    def changeColor(self, stickyNote, attribute):
        # always returns tuple with 2 objects such as: >((143, 194, 126), '#8fc27e')< or >(None, None)<
        
        colorCode = colorchooser.askcolor(
            initialcolor=stickyNote.settings[attribute], 
            title="Change " + attribute)[1]
        
        if not colorCode:
            return

        # update actual stickyNote and its titleLabel/frame
        if attribute == "BackgroundColor":
            stickyNote.textBox.config(bg=colorCode)
            stickyNote.titleLabel.config(bg=colorCode)

        elif attribute == "BarColor":
            stickyNote.parentWindow.config(bg=colorCode)
            stickyNote.aestheticBar.config(bg=colorCode)
            stickyNote.titleLabelFrame.config(highlightbackground=colorCode)

        elif attribute == "FontColor":
            stickyNote.textBox.config(fg=colorCode, insertbackground=colorCode)
            stickyNote.titleLabel.config(fg=colorCode)
        else:
            return
        
        # update settings dictionary
        stickyNote.settings[attribute] = colorCode

        # update database
        self.db.execute("\
            UPDATE STICKYNOTE\
            SET {} == '{}'\
            WHERE Title == '{}'".format(
                attribute,
                colorCode,
                stickyNote.title
                )
            )

    
    def toggleHubWindow(self):
        if self.parentWindow.winfo_viewable():
            self.parentWindow.iconify()
        else:
            self.parentWindow.deiconify()
        

    def toggleStickyNoteWindow(self, stickyNote):
        """Toggle "open" state of the stickyNote. Note that the closeWindow method removes stickyNotes from openStickyNotes and changes the toggleButton's image regardless."""
        
        if stickyNote.parentWindow.winfo_viewable():
            stickyNote.closeWindow()
        else:
            self.openStickyNotes.append(stickyNote)
            stickyNote.parentWindow.deiconify()
            stickyNote.toggleButton.config(
                image=self.toggleOnImage, text="on ")

    
    def prepareImage(self, directory, dimensions):

        # check if icon image is present and whether the PIL library is installed
        if path.exists(directory) and "PIL" in importedModules:
                preImage = Image.open(directory)
                
                preImage = preImage.resize(
                    dimensions, Image.Resampling.LANCZOS)
                
                preparedImage = ImageTk.PhotoImage(preImage)
        else:
            preparedImage=None

        return preparedImage


    def prepareImages(self, imageFileName, dimensions):
        """PIL explicitly requires assigning images into self variables, lest it not display correctly. The "exec" function enables the automation of assigning variables."""

        for image, fileName in imageFileName:
            exec(
                "self.{} = \
                self.prepareImage(self.parentDir + '/icons/{}', {})".format(
                    image,
                    fileName,
                    dimensions
                )
            )


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
            font=("Segoe UI", 35, "italic")
        )
        self.hubLabel.grid(row=self.currentRow, column=0, columnspan=6)


        self.newStickyNoteButton = tk.Button(
            self.contentFrame, 
            image=self.bdayPresentImage, text=" + ", 
            command=self.createNewStickyNote,
            font=15,
            bg="light green"
            )
        self.newStickyNoteButton.grid(row=self.currentRow, column=6, 
            pady=10)

        self.setHoverBackgroundBindings(
            self.newStickyNoteButton, "#00CC00", "light green")

        self.currentRow += 1


        # (re)/add every stickyNote's record into the resetted frame
        for stickyNote in self.allStickyNotes:
            self.updateHubContent(stickyNote)

    
    def adjustPositionXYvalues(self):
        """For my computer, TKinter's geometry method for window objects *always* set its position +8 and +31 units off for the X and Y coordinates respectively. Because I don't know whether this issue is computer dependent nor whether it will get fixed, AdjustPositionX/Y values are calculated every time."""

        # one stickyNote is guaranteed to exist at all times; IndexError is impossible
        stickyNote = self.openStickyNotes[0]

        # winfo_rootx and winfo_rooty don't work properly without window being updated beforehand
        stickyNote.parentWindow.update()
        
        self.adjustPositions = {
            'AdjustPositionX': 
            stickyNote.settings['PositionX'] - 
            stickyNote.parentWindow.winfo_rootx(),\
            \
            'AdjustPositionY': stickyNote.settings['PositionY'] - 
            stickyNote.parentWindow.winfo_rooty()
            }

        
    def setHoverBackgroundBindings(self, widget, enterColor, leaveColor):
        widget.bind('<Enter>', 
            lambda e: widget.config(bg=enterColor))

        widget.bind('<Leave>', 
            lambda e: widget.config(bg=leaveColor))
    

    def deleteStickyNote(self, stickyNote):
        """stickyNote.closeWindow() only withdraws a window. In this case, we want it destroyed completely."""

        confirmation = messagebox.askyesnocancel(
            "Are you sure?", "{} is to be deleted. This is an irreversible action.".format(
                stickyNote.title
            )
        )
        
        if not confirmation:
            return


        self.db.execute("\
            DELETE FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                stickyNote.title
            )
        )
        
        self.connector.commit()

        # if the application's already closed, no need to execute any further.
        if stickyNote in self.openStickyNotes and self.removeFromOpenStickyNotes(
            stickyNote):
            return
        
        self.allStickyNotes.remove(stickyNote)
        
        stickyNote.parentWindow.destroy()
        
        self.refreshHubContent()


    def insertDefaultStickyNote(self, title):
            """Called on empty database or when creating a new stickyNote."""

            self.db.execute(
                "INSERT INTO STICKYNOTE (Title)\
                VALUES (?)", [title]
            )


    def queryNewTitle(self, title, query):
        newTitle = simpledialog.askstring(
            title, query)

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
        
        self.db.execute("\
            SELECT * FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                newTitle
            )
        )
        
        if self.db.fetchone():
            messagebox.showerror(
                "IntegrityError", 
                "{} is already in use!".format(
                    newTitle
                )
            )
            return

        return newTitle


    def createNewStickyNote(self):
        newTitle = self.queryNewTitle("Add New stickyNote", "Create stickyNote~")

        if not newTitle:
            return
        

        self.insertDefaultStickyNote(newTitle)

        self.db.execute("\
            SELECT * FROM STICKYNOTE\
            WHERE Title == '{}'".format(
                newTitle
            )
        )
        
        newStickyNoteData = dict(self.db.fetchone())

        newStickyNote = StickyNoteWidget(
            tk.Toplevel(), newStickyNoteData['Title'], self)
        
        self.allStickyNotes.append(newStickyNote)
        self.openStickyNotes.append(newStickyNote)

        self.updateHubContent(newStickyNote)
        

    def removeFromOpenStickyNotes(self, stickyNote):
        """Remove stickyNote from openStickyNotes. Close the application if no stickyNotes are open anymore.

        Return True if application has indeed been closed. Otherwise, False."""
        
        self.openStickyNotes.remove(stickyNote)

        # if no stickyNotes are open anymore, close the whole application
        if self.openStickyNotes == []:
            self.closeApplication()
            return True
        
        return False
    
    
    def closeApplication(self):
        """Because StickyNoteHub is the "root" window to all of the Toplevel widgets (the actual stickyNotes), closing it will close everything else automatically."""

        for stickyNote in self.openStickyNotes:
            stickyNote.saveData()
        
        self.db.close()
        self.connector.close()

        self.parentWindow.destroy()


    def createSQLiteTables(self):
        self.db.execute("\
            CREATE TABLE STICKYNOTE(\
            ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            Title TEXT UNIQUE COLLATE NOCASE NOT NULL,\
            RawText TEXT NOT NULL DEFAULT 'Type here :D',\
            DimensionX INT NOT NULL DEFAULT 300,\
            DimensionY INT NOT NULL DEFAULT 200,\
            PositionX INT NOT NULL DEFAULT 400,\
            PositionY INT NOT NULL DEFAULT 400,\
            BackgroundColor VARCHAR(7) NOT NULL \
            DEFAULT '#093553' CHECK(BackgroundColor LIKE '#%'),\
            \
            BarColor VARCHAR(7) NOT NULL \
            DEFAULT '#2980B9' CHECK(BarColor LIKE '#%'),\
            \
            FontColor VARCHAR(7) NOT NULL \
            DEFAULT '#FFFFFF' CHECK(FontColor LIKE '#%'),\
            \
            FontFamily TEXT NOT NULL DEFAULT 'Segoe UI',\
            \
            FontSize INT NOT NULL \
            DEFAULT 12 CHECK(8 <= FontSize AND FontSize <= 50)\
            )")



if __name__ == "__main__":
    root = tk.Tk()

    StickyNoteHub(root)

    root.mainloop()