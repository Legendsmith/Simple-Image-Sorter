from cProfile import label
from operator import indexOf
import tkinter.font as tkfont
from turtle import color
from canvasimage import CanvasImage
import tkinter.scrolledtext as tkst
from tkinter.ttk import Panedwindow, Checkbutton
from PIL import Image, ImageTk
from functools import partial
from tktooltip import ToolTip
import tkinter.scrolledtext as tkst
import tkinter as tk
import logging
from tkinter.messagebox import askokcancel
from math import floor,sqrt
import random
import os
import pyvips
from tkinter import filedialog as tkFileDialog
import json

def luminance(hexin):
    color = tuple(int(hexin.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    r = color[0]
    g = color[1]
    b = color[2]
    hsp = sqrt(
        0.299 * (r**2) +
        0.587 * (g**2) +
        0.114 * (b**2)
    )
    if hsp > 115.6:
        return 'light'
    else:
        return 'dark'


def disable_event():
    pass

def randomColor():
    color = '#'
    hexletters = '0123456789ABCDEF'
    for i in range(0, 6):
        color += hexletters[floor(random.random()*16)]
    return color

def saveprefs(manager, gui):
    if os.path.exists(gui.sdpEntry.get()):
        sdp = gui.sdpEntry.get()
    else:
        sdp = ""
    if os.path.exists(gui.ddpEntry.get()):
        ddp = gui.ddpEntry.get()
    else:
        ddp = ""
    save = {"srcpath": sdp, "despath": ddp, "exclude": manager.exclude, "hotkeys": gui.hotkeys, "thumbnailsize": gui.thumbnailsize, "threads": manager.threads, "hideonassign": gui.hideonassignvar.get(
    ), "hidemoved": gui.hidemovedvar.get(), "squaresperpage": gui.squaresperpage.get(), "geometry": gui.winfo_geometry(), "lastsession": gui.sessionpathvar.get(),"autosave":manager.autosave}
    try:
        with open("prefs.json", "w+") as savef:
            json.dump(save, savef,indent=4, sort_keys=True)
            logging.debug(save)
    except Exception as e:
        logging.warning(("Failed to save prefs:", e))
    try:
        if manager.autosave:
            manager.savesession(False)
    except Exception as e:
        logging.warning(("Failed to save session:", e))


class GUIManager(tk.Tk):
    thumbnailsize = 256
    def __init__(self, fileManager) -> None:
        super().__init__()
        # variable initiation
        self.gridsquarelist = []
        self.hideonassignvar = tk.BooleanVar()
        self.hideonassignvar.set(True)
        self.hidemovedvar = tk.BooleanVar()
        self.showhiddenvar = tk.BooleanVar()
        self.squaresperpage = tk.IntVar()
        self.squaresperpage.set(120)
        self.sessionpathvar = tk.StringVar()
        self.imagewindowgeometry = str(int(self.winfo_screenwidth(
        )*0.80)) + "x" + str(self.winfo_screenheight()-120)+"+365+60"
        # store the reference to the file manager class.
        self.fileManager = fileManager
        self.geometry(str(self.winfo_screenwidth()-5)+"x" +
                      str(self.winfo_screenheight()-120))
        self.geometry("+0+60")
        self.buttons = []
        self.hotkeys = "123456qwerty7890uiop[asdfghjkl;zxcvbnm,.!@#$%^QWERT&*()_UIOPASDFGHJKLZXCVBNM<>"
        # Paned window that holds the almost top level stuff.
        self.toppane = Panedwindow(self, orient="horizontal")
        # Frame for the left hand side that holds the setup and also the destination buttons.
        self.leftui = tk.Frame(self.toppane)
        #self.leftui.grid(row=0, column=0, sticky="NESW")
        self.leftui.columnconfigure(0, weight=1)
        self.toppane.add(self.leftui, weight=1)
        self.panel = tk.Label(self.leftui, wraplength=300, justify="left", text="""Select a source directory to search for images in above.
The program will find all png, gif, jpg, bmp, pcx, tiff, Webp, and psds. It can has as many sub-folders as you like, the program will scan them all (except exclusions).
Enter a root folder to sort to for the "Destination field" too. The destination directory MUST have sub folders, since those are the folders that you will be sorting to.
\d (unless you delete prefs.json). Remember that it's one per line, no commas or anything.
You can change the hotkeys in prefs.json, just type a string of letters and numbers and it'll use that. It differentiates between lower and upper case (anything that uses shift), but not numpad.

By default the program will only load a portion of the images in the folder for performance reasons. Press the "Add Files" button to make it load another chunk. You can configure how many it adds and loads at once in the program.  

Right-click on Destination Buttons to show which images are assigned to them. (Does not show those that have already been moved)  
Right-click on Thumbnails to show a zoomable full view. You can also **rename** images from this view.  

Thanks to FooBar167 on stackoverflow for the advanced (and memory efficient!) Zoom and Pan tkinter class.
Thank you for using this program!""")
        self.panel.grid(row=1, column=0, columnspan=200,
                        rowspan=200, sticky="NSEW")

        self.columnconfigure(0, weight=1)
        self.buttonframe = tk.Frame(master=self.leftui)
        self.buttonframe.grid(
            column=0, row=1, sticky="NSEW")
        self.buttonframe.columnconfigure(0, weight=1)
        self.entryframe = tk.Frame(master=self.leftui)
        self.entryframe.columnconfigure(1, weight=1)
        self.sdpEntry = tk.Entry(
            self.entryframe, takefocus=False)  # scandirpathEntry
        self.ddpEntry = tk.Entry(
            self.entryframe, takefocus=False)  # dest dir path entry

        sdplabel = tk.Button(
            self.entryframe, text="Source Folder:", command=partial(self.filedialogselect, self.sdpEntry, "d"))
        ddplabel = tk.Button(
            self.entryframe, text="Destination Folder:", command=partial(self.filedialogselect, self.ddpEntry, "d"))
        self.activebutton = tk.Button(
            self.entryframe, text="New Session", command=partial(fileManager.validate, self))
        ToolTip(self.activebutton,delay=1,msg="Start a new Session with the entered source and destination")
        self.loadpathentry = tk.Entry(
            self.entryframe, takefocus=False, textvariable=self.sessionpathvar)
        self.loadbutton = tk.Button(
            self.entryframe, text="Load Session", command=self.fileManager.loadsession)
        ToolTip(self.loadbutton,delay=1,msg="Load and start the selected session data.")
        loadfolderbutton = tk.Button(self.entryframe, text="Session Data:", command=partial(
            self.filedialogselect, self.loadpathentry, "f"))
        ToolTip(loadfolderbutton,delay=1,msg="Select a session json file to open.")
        loadfolderbutton.grid(row=3, column=0, sticky='e')
        self.loadbutton.grid(row=3, column=2, sticky='ew')
        self.loadpathentry.grid(row=3, column=1, sticky='ew', padx=2)
        sdplabel.grid(row=0, column=0, sticky="e")
        self.sdpEntry.grid(row=0, column=1, sticky="ew", padx=2)
        ddplabel.grid(row=1, column=0, sticky="e")
        self.ddpEntry.grid(row=1, column=1, sticky="ew", padx=2)
        self.activebutton.grid(row=1, column=2, sticky="ew")
        self.excludebutton = tk.Button(
            self.entryframe, text="Manage Exclusions", command=self.excludeshow)
        self.excludebutton.grid(row=0, column=2)
        # show the entry frame, sticky it to the west so it mostly stays put.
        self.entryframe.grid(row=0, column=0, sticky="ew")
        # Finish setup for the left hand bar.
        # Start the grid setup
        imagegridframe = tk.Frame(self.toppane)
        imagegridframe.grid(row=0, column=1, sticky="NSEW")
        self.imagegrid = tk.Text(
            imagegridframe, wrap='word', borderwidth=0, highlightthickness=0, state="disabled", background='#a9a9a9')
        vbar = tk.Scrollbar(imagegridframe, orient='vertical',
                            command=self.imagegrid.yview)
        vbar.grid(row=0, column=1, sticky='ns')
        self.imagegrid.configure(yscrollcommand=vbar.set)
        self.imagegrid.grid(row=0, column=0, sticky="NSEW")
        imagegridframe.rowconfigure(0, weight=1)
        imagegridframe.columnconfigure(0, weight=1)

        self.toppane.add(imagegridframe, weight=3)
        self.toppane.grid(row=0, column=0, sticky="NSEW")
        self.toppane.configure()
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=0)
        self.protocol("WM_DELETE_WINDOW", self.closeprogram)
        self.winfo_toplevel().title("Simple Image Sorter: Multiview Edition v2.4")
        self.leftui.bind("<Configure>", self.buttonResizeOnWindowResize)
        self.buttonResizeOnWindowResize("a")

    def isnumber(self, char):
        return char.isdigit()

    def showall(self):
        for x in self.fileManager.imagelist:
            if x.guidata["show"] == False:
                x.guidata["frame"].grid()
        self.hidemoved()
        self.hideassignedsquare(self.fileManager.imagelist)

    def closeprogram(self):
        if self.fileManager.hasunmoved:
            if askokcancel("Designated but Un-Moved files, really quit?","You have destination designated, but unmoved files. (Simply cancel and Move All if you want)"):
                saveprefs(self.fileManager, self)
                self.destroy()
                exit(0)
        else:
            saveprefs(self.fileManager, self)
            self.destroy()
            exit(0)


    def excludeshow(self):
        excludewindow = tk.Toplevel()
        excludewindow.winfo_toplevel().title(
            "Folder names to ignore, one per line. This will ignore sub-folders too.")
        excludetext = tkst.ScrolledText(excludewindow)
        for x in self.fileManager.exclude:
            excludetext.insert("1.0", x+"\n")
        excludetext.pack()
        excludewindow.protocol("WM_DELETE_WINDOW", partial(
            self.excludesave, text=excludetext, toplevelwin=excludewindow))

    def excludesave(self, text, toplevelwin):
        text = text.get('1.0', tk.END).splitlines()
        exclude = []
        for line in text:
            exclude.append(line)
        self.fileManager.exclude = exclude
        try:
            toplevelwin.destroy()
        except:
            pass


    def tooltiptext(self,imageobject):
        text=""
        if imageobject.dupename:
            text += "Image has Duplicate Filename!\n"
        text += "Leftclick to select this for assignment. Rightclick to open full view"
        return text

    def makegridsquare(self, parent, imageobj, setguidata):
        frame = tk.Frame(parent, width=self.thumbnailsize +
                         14, height=self.thumbnailsize+24)
        frame.obj = imageobj
        try:
            if setguidata:
                if not os.path.exists(imageobj.thumbnail):
                    self.fileManager.makethumb(imageobj)
                try:
                    buffer = pyvips.Image.new_from_file(imageobj.thumbnail)
                    img = ImageTk.PhotoImage(Image.frombuffer(
                        "RGB", [buffer.width, buffer.height], buffer.write_to_memory()))
                except:  # Pillow fallback
                    img = ImageTk.PhotoImage(Image.open(imageobj.thumbnail))
            else:
                img = imageobj.guidata['img']

            canvas = tk.Canvas(frame, width=self.thumbnailsize,
                               height=self.thumbnailsize)
            tooltiptext=tk.StringVar(frame,self.tooltiptext(imageobj))
            ToolTip(canvas,msg=tooltiptext.get,delay=1)
            canvas.create_image(
                self.thumbnailsize/2, self.thumbnailsize/2, anchor="center", image=img)
            check = Checkbutton(
                frame, textvariable=imageobj.name, variable=imageobj.checked, onvalue=True, offvalue=False)
            canvas.grid(column=0, row=0, sticky="NSEW")
            check.grid(column=0, row=1, sticky="N")
            frame.rowconfigure(0, weight=4)
            frame.rowconfigure(1, weight=1)
            frame.config(height=self.thumbnailsize+12)
            if(setguidata):  # save the data to the image obj to both store a reference and for later manipulation
                imageobj.setguidata(
                    {"img": img, "frame": frame, "canvas": canvas, "check": check, "show": True,"tooltip":tooltiptext})
            # anything other than rightclicking toggles the checkbox, as we want.
            canvas.bind("<Button-1>", partial(bindhandler, check, "invoke"))
            canvas.bind(
                "<Button-3>", partial(self.displayimage, imageobj))
            check.bind("<Button-3>", partial(self.displayimage, imageobj))
            canvas.bind("<MouseWheel>", partial(
                bindhandler, parent, "scroll"))
            frame.bind("<MouseWheel>", partial(
                bindhandler, self.imagegrid, "scroll"))
            check.bind("<MouseWheel>", partial(
                bindhandler, self.imagegrid, "scroll"))
            if imageobj.moved:
                frame.configure(
                    highlightbackground="green", highlightthickness=2)
                if os.path.dirname(imageobj.path) in self.fileManager.destinationsraw:
                    color = self.fileManager.destinations[indexOf(
                        self.fileManager.destinationsraw,os.path.dirname(imageobj.path))]['color']
                    frame['background'] = color
                    canvas['background'] = color
            frame.configure(height=self.thumbnailsize+10)
            if imageobj.dupename:
                frame.configure(
                    highlightbackground="yellow", highlightthickness=2)
        except Exception as e:
            logging.error(e)
        return frame

    def displaygrid(self, imagelist, range):
        for i in range:
            gridsquare = self.makegridsquare(
                self.imagegrid, imagelist[i], True)
            self.gridsquarelist.append(gridsquare)
            self.imagegrid.window_create("insert", window=gridsquare)

    def buttonResizeOnWindowResize(self, b=""):
        if len(self.buttons) > 0:
            for x in self.buttons:
                x.configure(wraplength=(self.buttons[0].winfo_width()-1))
    
    def displayimage(self, imageobj, a):
        path = imageobj.path
        if hasattr(self, 'imagewindow'):
            self.imagewindow.destroy()
        
        self.imagewindow = tk.Toplevel()
        imagewindow = self.imagewindow
        imagewindow.rowconfigure(1, weight=1)
        imagewindow.columnconfigure(0, weight=1)
        imagewindow.wm_title("Image: " + path)
        imagewindow.geometry(self.imagewindowgeometry)
        imageframe = CanvasImage(imagewindow, path)
        # takes the smaller scale (since that will be the limiting factor) and rescales the image to that so it fits the frame.
        imageframe.rescale(min(imagewindow.winfo_width(
        )/imageframe.imwidth, imagewindow.winfo_height()/imageframe.imheight))
        imageframe.grid(column=0, row=1)
        imagewindow.bind(
            "<Button-3>", partial(bindhandler, imagewindow, "destroy"))
        renameframe = tk.Frame(imagewindow)
        renameframe.columnconfigure(1, weight=1)
        namelabel = tk.Label(renameframe, text="Image Name:")
        namelabel.grid(column=0, row=0, sticky="W")
        nameentry = tk.Entry(
            renameframe, textvariable=imageobj.name, takefocus=False)
        nameentry.grid(row=0, column=1, sticky="EW")

        renameframe.grid(column=0, row=0, sticky="EW")
        imagewindow.protocol("WM_DELETE_WINDOW", self.saveimagewindowgeo)
        imagewindow.obj = imageobj

    def saveimagewindowgeo(self):
        self.imagewindowgeometry = self.imagewindow.winfo_geometry()
        self.checkdupename(self.imagewindow.obj)
        self.imagewindow.destroy()

    def filedialogselect(self, target, type):
        if type == "d":
            path = tkFileDialog.askdirectory()
        elif type == "f":
            d = tkFileDialog.askopenfile(initialdir=os.getcwd(
            ), title="Select Session Data File", filetypes=(("JavaScript Object Notation", "*.json"),))
            path = d.name
        if isinstance(target, tk.Entry):
            target.delete(0, tk.END)
            target.insert(0, path)

    def guisetup(self, destinations):
        sdpEntry = self.sdpEntry
        ddpEntry = self.ddpEntry
        sdpEntry.config(state=tk.DISABLED)
        ddpEntry.config(state=tk.DISABLED)
        panel = self.panel
        buttonframe = self.buttonframe
        hotkeys = self.hotkeys
        for key in hotkeys:
            self.unbind_all(key)
        for x in self.buttons:
            x.destroy()  # clear the gui
        panel.destroy()
        guirow = 1
        guicol = 0
        itern = 0
        smallfont = tkfont.Font(family='Helvetica', size=10)
        columns = 1
        if len(destinations) > int((self.leftui.winfo_height()/35)-2):
            columns=2
            buttonframe.columnconfigure(1, weight=1)
        if len(destinations) > int((self.leftui.winfo_height()/15)-4):
            columns = 3
            buttonframe.columnconfigure(2, weight=1)
        for x in destinations:
            color = x['color']
            if x['name'] != "SKIP" and x['name'] != "BACK":
                if(itern < len(hotkeys)):
                    newbut = tk.Button(buttonframe, text=hotkeys[itern] + ": " + x['name'], command=partial(
                        self.fileManager.setDestination, x, {"widget": None}), anchor="w", wraplength=(self.leftui.winfo_width()/columns)-1)
                    self.bind_all(hotkeys[itern], partial(
                        self.fileManager.setDestination, x))
                    fg = 'white'
                    if luminance(color) == 'light':
                        fg = "black"
                    newbut.configure(bg=color, fg=fg)
                    if(len(x['name']) >= 13):
                        newbut.configure(font=smallfont)
                else:
                    newbut = tk.Button(buttonframe, text=x['name'], command=partial(
                        self.fileManager.setDestination, x, {"widget": None}), anchor="w")
                itern += 1
            newbut.config(font=("Courier", 12), width=int(
                (self.leftui.winfo_width()/12)/columns), height=1)
            ToolTip(newbut,msg="Rightclick to show images assigned to this destination",delay=1)
            if len(x['name']) > 20:
                newbut.config(font=smallfont)
            newbut.dest = x
            if guirow > ((self.leftui.winfo_height()/35)-2):
                guirow = 1
                guicol += 1
            newbut.grid(row=guirow, column=guicol, sticky="nsew")
            newbut.bind("<Button-3>", partial(self.showthisdest, x))

            self.buttons.append(newbut)
            guirow += 1
        self.entryframe.grid_remove()
        # options frame
        optionsframe = tk.Frame(self.leftui)
        # have this just get checked when setting dstination then hide or not
        hideonassign = tk.Checkbutton(optionsframe, text="Hide Assigned",
                                      variable=self.hideonassignvar, onvalue=True, offvalue=False)
        hideonassign.grid(column=0, row=0, sticky='W')
        ToolTip(hideonassign,delay=1,msg="When checked, images that are assigned to a destination be hidden from the grid.")
        showhidden = tk.Checkbutton(optionsframe, text="Show Hidden Images",
                                    variable=self.showhiddenvar, onvalue=True, offvalue=False, command=self.showhiddensquares)
        showhidden.grid(column=0, row=1, sticky="W")
        hidemoved = tk.Checkbutton(optionsframe, text="Hide Moved",
                                   variable=self.hidemovedvar, onvalue=True, offvalue=False, command=self.hidemoved)
        hidemoved.grid(column=1, row=1, sticky="w")
        ToolTip(hidemoved,delay=1,msg="When checked, images that are moved will be hidden from the grid.")
        self.showhidden = showhidden
        self.hideonassign = hideonassign
        valcmd = self.register(self.isnumber)
        squaresperpageentry = tk.Entry(
            optionsframe, textvariable=self.squaresperpage, validate="key", validatecommand=(valcmd, "%P"), takefocus=False)
        ToolTip(squaresperpageentry,delay=1,msg="How many more images to add when Load Images is clicked")
        for n in range(0, itern):
            squaresperpageentry.unbind(hotkeys[n])
        addpagebut = tk.Button(
            optionsframe, text="Load More Images", command=self.addpage)

        ToolTip(addpagebut,msg="Add another batch of files from the source folders.", delay=1)

        squaresperpageentry.grid(row=2, column=0, sticky="E")
        addpagebut.grid(row=2, column=1, sticky="EW")
        self.addpagebutton = addpagebut
        hideonassign.grid(column=1, row=0)
        # save button
        savebutton = tk.Button(optionsframe,text="Save Session",command=partial(self.fileManager.savesession,True))
        ToolTip(savebutton,delay=1,msg="Save this image sorting session to a file, where it can be loaded at a later time. Assigned destinations and moved images will be saved.")
        savebutton.grid(column=0,row=0,sticky="ew")
        moveallbutton = tk.Button(
            optionsframe, text="Move All", command=self.fileManager.moveall)
        moveallbutton.grid(column=1, row=3, sticky="EW")
        ToolTip(moveallbutton,delay=1,msg="Move all images to their assigned destinations, if they have one.")
        clearallbutton = tk.Button(
            optionsframe, text="Clear Selection", command=self.fileManager.clear)
        ToolTip(clearallbutton,delay=1,msg="Clear your selection on the grid and any other windows with checkable image grids.")
        clearallbutton.grid(row=3, column=0, sticky="EW")
        optionsframe.columnconfigure(0, weight=1)
        optionsframe.columnconfigure(1, weight=3)  
        self.optionsframe = optionsframe
        self.optionsframe.grid(row=0, column=0, sticky="ew")
        self.bind_all("<Button-1>", self.setfocus)

    def setfocus(self, event):
        event.widget.focus_set()

    # todo: make 'moved' and 'assigned' lists so the show all etc just has to iterate over those.

    def hideassignedsquare(self, imlist):
        if self.hideonassignvar.get():
            for x in imlist:
                if x.dest != "":
                    self.imagegrid.window_configure(
                        x.guidata["frame"], window='')
                    x.guidata["show"] = False

    def hideallsquares(self):
        for x in self.gridsquarelist:
            self.imagegrid.window_configure(x, window="")

    def showhiddensquares(self):
        if self.showhiddenvar.get():
            for x in self.gridsquarelist:
                try:
                    x.obj.guidata["frame"] = x
                    self.imagegrid.window_create("insert", window=x)
                except:
                    pass

        else:
            self.hideassignedsquare(self.fileManager.imagelist)
            self.hidemoved()

    def showunassigned(self, imlist):
        for x in imlist:
            if x.guidata["show"] or x.dest == "":
                self.imagegrid.window_create(
                    "insert", window=x.guidata["frame"])

    def showthisdest(self, dest, *args):
        destwindow = tk.Toplevel()
        destwindow.geometry(str(int(self.winfo_screenwidth(
        )*0.80)) + "x" + str(self.winfo_screenheight()-120)+"+365+60")
        destwindow.winfo_toplevel().title(
            "Files designated for" + dest['path'])
        destgrid = tk.Text(destwindow, wrap='word', borderwidth=0,
                           highlightthickness=0, state="disabled", background='#a9a9a9')
        destgrid.grid(row=0, column=0, sticky="NSEW")
        destwindow.columnconfigure(0, weight=1)
        destwindow.rowconfigure(0, weight=1)
        vbar = tk.Scrollbar(destwindow, orient='vertical',
                            command=destgrid.yview)
        vbar.grid(row=0, column=1, sticky='ns')
        for x in self.fileManager.imagelist:
            if x.dest == dest['path']:
                newframe = self.makegridsquare(destgrid, x, False)
                destgrid.window_create("insert", window=newframe)

    def hidemoved(self):
        if self.hidemovedvar.get():
            for x in self.fileManager.imagelist:
                if x.moved:
                    try:
                        self.imagegrid.window_configure(
                            x.guidata["frame"], window='')
                    except Exception as e:
                        #logging.error(e)
                        pass

    def addpage(self, *args):
        filelist = self.fileManager.imagelist
        if len(self.gridsquarelist) < len(filelist)-1:
            listmax = min(len(self.gridsquarelist) +
                          self.squaresperpage.get(), len(filelist)-1)
            ran = range(len(self.gridsquarelist), listmax)
            sublist = filelist[ran[0]:listmax]
            self.fileManager.generatethumbnails(sublist)
            self.displaygrid(self.fileManager.imagelist, ran)
        else:
            self.addpagebutton.configure(text="No More Images!",background="#DD3333")

    def checkdupename(self, imageobj):
        if imageobj.name.get() in self.fileManager.existingnames:
            imageobj.dupename=True
            imageobj.guidata["frame"].configure(
                    highlightbackground="yellow", highlightthickness=2)
        else:
            imageobj.dupename=False
            imageobj.guidata["frame"].configure(highlightthickness=0)
            self.fileManager.existingnames.add(imageobj.name.get())
        imageobj.guidata['tooltip'].set(self.tooltiptext(imageobj))

def bindhandler(*args):
    widget = args[0]
    command = args[1]
    if command == "invoke":
        widget.invoke()
    elif command == "destroy":
        widget.destroy()
    elif command == "scroll":
        widget.yview_scroll(-1*floor(args[2].delta/120), "units")
