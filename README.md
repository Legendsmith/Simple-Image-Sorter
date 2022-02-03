# Simple-Image-Sorter
Sorts images into destination files. Written in python. I got really sick of organising my character art and meme folders by hand.

## USE
- Make sure all your files that you want to sort are in some kind of directory/folder already, they can be in folders within that folder, the program will scan them all
-- (There is an 'exclusions' function where you can list folder names to ignore.
- Within a new or existing folder, create your new organisational structure, _for example:_
```
Pictures
├ Family
├ Holiday
├ Wedding
├ My stuff
├ Misc
```
- Select your new root folder ("Pictures", in the above example) as the ``'destination'``, and the folder that contains all the existing pictures you want to sort as the ``source``. Note these *cannot* be the same folder. They must be different structures.
- Press Ready!
Designate images by clicking on them, then assign them to destinations with the corresponding destination button. When you're ready, click "move all" to move everything at once.

By default the program will only load a portion of the images in the folder for performance reasons. Press the "Add Files" button to make it load another chunk. You can configure how many it adds and loads at once in the program.  
- Right-click on Destination Buttons to show which images are assigned to them. (Does not show those that have already been moved)  
- Right-click on Thumbnails to show a zoomable full view. You can also **rename** images from this view.  
- You can configure the size of thumbnails in prefs.json. Default is 256px.
- The program will save your session automatically on exit with the name of source and destination folders, this WILL overwrite.
- You can save your session manually too with a filename, and load it later to resume where you last left off.

There are hotkeys and buttons for the folders to sort into, which are essentially your categories, and you can customise hotkeys (though you'll need to restart the program). Hotkeys can be customized in prefs.json

Thanks to FooBar167 on stackoverflow for the advanced (and memory efficient!) Zoom and Pan tkinter class. Thank you for using this program.
