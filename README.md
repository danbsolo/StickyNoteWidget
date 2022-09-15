# StickyNoteWidget
A virtual sticky note to be placed on a Windows desktop using Python's Tkinter module.

<p align="center">
  <img src="images/initialExample.JPG" alt="Example of Sticky Note Widget in action">
</p>

## What's New?
- Fixed the code's _style_ to something more readable. Includes making comments more insightful, better whitespace usage, etc. Also changed the names of several files, mostly removing underscores in favor of CamelCase.

## Old Changes
- Converted StickyNoteWidget from a Procedural Program into an Object-Oriented Program (OOP). This will streamline debugging, adding new features, updating the code style, etc. _Does not change functionality._

## How to Install
1. Ensure Python is installed along with the Tkinter library, which is typically included by default.
2. Create an _Environment Variable_ called `StickyNoteWidgetData`. Its value should be the location of the folder where both `StickyNoteWidget.py` and `textFiles` are stored. For example, your value may be: `C:/Users/NAME/Desktop/widgets/StickyNoteWidget/`. 
**Must be forward slashes, not back slashes. Must end in a forward slash.**

## Features
- Automatically saves text, size, and location of window upon typing or clicking the `X` button. No need to manually save.
- Automatically saves a backup for each day of the week, 7 backups in total.
- Easily change attributes such as font size in `textFiles/1/immutableConfig.txt`.

<p align="center">
  <img src="images/attributeChangeExample.JPG" alt="Example of changed attributes">
</p>

## Known Issues
- Cannot handle certain characters well, such as emojis
- Cannot boldface, italics, etc. for specific snippets of text. It's either all or nothing.
- Cannot change color of the cursor (it stays black).
- Spawns a useless black box (Python's terminal window) if opening outside the context of an IDE.
- Text may not wrap around the window properly.
- The x and y attributes slightly save the location of the window incorrectly, only solved with `xAdjust` and `yAdjust` in `immutableConfig.txt`.
- Putting the widget into `ORR mode` renders it impossible to move or close through normal methods; requires ending the task manually in task manager.
- An extremely rare glitch can occur where the window will spawn outside the bounds of the desktop screen, resulting in it being inaccessible. Fixing this requires one to change the location of the file manually in `config.txt` to something manageable such as `451x257+213+202`.