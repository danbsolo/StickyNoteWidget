# Sticky Note Widget
A sticky note to be placed on the Windows desktop using Python's Tkinter module.

<p align="center">
  <img src="images/initialExample.JPG" alt="Example of Sticky Note Widget in action">
</p>

## Project Origin
For a course's final project, the task description read: "All that we ask is that you build something of interest to you, that you solve an actual problem, that you impact your community, or that you change the world. **Strive to create something that outlives this course.**" Here we are.

## Preface
This project is still very much in beta, much of the code hanging by a thread along with inadequate style. I aim to fix its shortcomings in the near future, but for now, the requirements are a little obtuse.

## How to Install
1. Ensure Python is installed along with the Tkinter library, which is typically included by default.
2. Create an *Environment Variable* called `TRACKER_FILES`. Its value should be the location of the folder where both `tracker.py` and `tracker_texts` are stored. For example, your value may be: `C:/Users/NAME/Desktop/widgets/`. 
Must be forward slashes, not back slashes. Must end in a forward slash.

## Features
- Automatically saves text, size, and location of window upon typing or clicking the `X` button. No need to manually save.
- Automatically saves a backup for each day of the week, 7 backups in total.
- Easily change attributes such as font size in `tracker_texts/1/immutable_configuration.txt`.

<p align="center">
  <img src="images/attributeChangeExample.JPG" alt="Example of changed attributes">
</p>

## Known Issues
- Cannot handle certain characters well, such as emojis
- Cannot change color of the font text line.
- Spawns a useless black box if opening outside the context of an IDE (Python's terminal window).
- New size and location may be lost if user doesn't either type something or click `X` button to save the configuration; e.g., shutting down the computer or clicking the terminal's `X` button instead.
- Text does not always wrap around the window properly.
- The border size on the left, bottom, and right sides of the window are incongruent.
- The x and y attributes slightly save the location of the window incorrectly, only solved with `rootx_adjust` and `rooty_adjust` in `immutable_configuration.txt`.
- Putting the widget into `ORR mode` renders it impossible to close through normal methods; requires ending the task manually in task manager.
- An extremely rare glitch can occur where the window will spawn outside the bounds of the desktop screen, resulting in it being inaccessible. Fixing this requires one to change the location of the file manually in `configuration.txt` to something manageable such as `451x257+213+202`.