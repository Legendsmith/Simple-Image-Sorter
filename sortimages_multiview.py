import math
import os
from sys import exit
import textwrap
from shutil import move as shmove
import tkinter as tk
import tkinter.scrolledtext as tkst
from tkinter.ttk import Panedwindow, Checkbutton
from PIL import Image, ImageTk
from functools import partial
from math import floor
import json
import random
from math import floor, sqrt
from tkinter import filedialog as tkFileDialog
import tkinter.font as tkfont
from collections import deque
from canvasimage import CanvasImage
import concurrent.futures as concurrent
import logging
from hashlib import md5
import pyvips


class Imagefile:
    name = ""
    path = ""
    dest = ""
    moved = False

    def __init__(self, name, path) -> None:
        self.name = name
        self.path = path
        self.checked = tk.IntVar(value=0)

    def move(self) -> str:
        destpath = self.dest
        if destpath != "" and os.path.isdir(destpath):
            try:
                shmove(self.path, os.path.join(destpath, self.name))
                self.moved = True
                self.guidata["frame"].configure(
                    highlightbackground="green", highlightthickness=2)
                self.path = os.path.join(destpath, self.name)
                returnstr = ("Moved:" + self.name + " -> " + destpath)
                destpath = ""
                return returnstr
            except Exception as e:
                logging.error("Error moving: %s . File: %s", e, self.name)
                return ("Error moving: %s . File: %s", e, self.name)

    def setid(self, id):
        self.id = id

    def setguidata(self, data):
        self.guidata = data

    def setdest(self, dest):
        self.dest = dest["path"]
        logging.debug("Set destination of %s to %s", self.name, self.dest)


def disable_event():
    pass


def randomColor():
    color = '#'
    hexletters = '0123456789ABCDEF'
    for i in range(0, 6):
        color += hexletters[floor(random.random()*16)]
    return color


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


def saveprefs(manager, gui):
    if os.path.exists(gui.sdpEntry.get()):
        sdp = gui.sdpEntry.get()
    else:
        sdp = ""
    if os.path.exists(gui.ddpEntry.get()):
        ddp = gui.ddpEntry.get()
    else:
        ddp = ""
    save = {"srcpath": sdp, "despath": ddp, "exclude": manager.exclude, "hotkeys": gui.hotkeys,
            "thumbnailgrid": gui.thumbnailgrid, "thumbnailsize": gui.thumbnailsize, "threads": manager.threads}
    try:
        with open("prefs.json", "w+") as savef:
            json.dump(save, savef)
            logging.debug(save)
    except Exception:
        pass


def bindhandler(*args):
    widget = args[0]
    command = args[1]
    if command == "invoke":
        widget.invoke()
    elif command == "destroy":
        widget.destroy()
    elif command == "scroll":
        widget.yview_scroll(-1*math.floor(args[2].delta/120), "units")


class GUIManager(tk.Tk):
    thumbnailgrid = [3, 3]
    thumbnailsize = 256

    def __init__(self, fileManager) -> None:
        super().__init__()
        self.gridsquarelist = []
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
        self.leftui.grid(row=0, column=0, sticky="NESW")
        self.leftui.columnconfigure(0, weight=1)
        self.leftui.columnconfigure(1, weight=1)
        self.leftui.columnconfigure(2, weight=1)
        self.toppane.add(self.leftui, weight=1)
        self.panel = tk.Label(self.leftui, wraplength=300, justify="left", text="""Select a source directory to search for images in above.
The program will find all png, gif, jpg, bmp, pcx, tiff, Webp, and psds. It can has as many sub-folders as you like, the program will scan them all (except exclusions).
Enter a root folder to sort to for the "Destination field" too. The destination directory MUST have sub folders, since those are the folders that you will be sorting to.
It is reccomended that the folder names are not super long. You can always rename them later if you desire longer names. Exclusions let you ignore folder names. They are saved (unless you delete prefs.json). Remember that it's one per line, no commas or anything.
You can change the hotkeys in prefs.json, just type a string of letters and numbers and it'll use that. It differentiates between lower and upper case (anything that uses shift), but not numpad.
Thanks to FooBar167 on stackoverflow for the advanced (and memory efficient!) Zoom and Pan tkinter class.
Rightclick a thumbnail to show the full image. You can use arrow keys or click and drag to pan the popout image. Mouse Wheel Zooms the image.
Thanks you for using this program!""")
        self.panel.grid(row=11, column=0, columnspan=200,
                        rowspan=200, sticky="NSEW")

        self.columnconfigure(0, weight=1)
        self.buttonframe = tk.Frame(master=self.leftui)
        self.buttonframe.grid(
            column=0, row=1, sticky="NSEW", rowspan=2, columnspan=3,)
        self.buttonframe.columnconfigure(0, weight=1)
        self.buttonframe.columnconfigure(1, weight=1)
        self.buttonframe.columnconfigure(2, weight=1)
        self.entryframe = tk.Frame(master=self.leftui)
        self.sdpEntry = tk.Entry(self.entryframe)  # scandirpathEntry
        self.ddpEntry = tk.Entry(self.entryframe)  # dest dir path entry

        self.sdplabel = tk.Button(
            self.entryframe, text="Source Folder:", command=partial(self.folderselect, "src"))
        self.ddplabel = tk.Button(
            self.entryframe, text="Destination Folder:", command=partial(self.folderselect, "des"))
        self.activebutton = tk.Button(
            self.entryframe, text="Ready", command=partial(fileManager.validate, self))

        self.sdplabel.grid(row=0, column=0, sticky="e")
        self.sdpEntry.grid(row=0, column=1, sticky="w")
        self.ddplabel.grid(row=1, column=0, sticky="e")
        self.ddpEntry.grid(row=1, column=1, sticky="w")
        self.activebutton.grid(row=1, column=2, sticky="ew")
        self.excludebutton = tk.Button(
            self.entryframe, text="Manage Exclusions", command=self.excludeshow)
        self.excludebutton.grid(row=0, column=2)
        # show the entry frame, sticky it to the west so it mostly stays put.
        self.entryframe.grid(row=0, column=0, sticky="w")
        # Finish setup for the left hand bar.
        # Start the grid setup
        imagegridframe = tk.Frame(self.toppane)
        imagegridframe.grid(row=0, column=1, sticky="NSEW")
        self.imagegrid = tk.Text(
            imagegridframe, wrap='word', borderwidth=0, highlightthickness=0, state="disabled")
        vbar = tk.Scrollbar(imagegridframe, orient='vertical',
                            command=self.imagegrid.yview)
        vbar.grid(row=0, column=1, sticky='ns')
        self.imagegrid.configure(yscrollcommand=vbar.set)
        # set background color to a darker grey
        self.imagegrid['background'] = '#a9a9a9'
        self.imagegrid.grid(row=0, column=0, sticky="NSEW")
        imagegridframe.rowconfigure(0, weight=1)
        imagegridframe.columnconfigure(0, weight=1)

        self.toppane.add(imagegridframe, weight=3)
        self.toppane.grid(row=0, column=0, columnspan=200,
                          rowspan=200, sticky="NSEW")
        self.toppane.configure()
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=0)
        self.protocol("WM_DELETE_WINDOW", self.closeprogram)
        self.winfo_toplevel().title("Simple Image Sorter v2.0")
        self.leftui.bind("<Configure>", self.buttonResizeOnWindowResize)
        self.buttonResizeOnWindowResize("a")
        # options frame
        optionsframe = tk.Frame(self.leftui)
        # have this just get checked when setting dstination then hide or not
        self.hideonassignvar = tk.BooleanVar()
        self.hideonassignvar.set(True)
        hideonassign = tk.Checkbutton(optionsframe, text="Hide Images Upon assigning destination",
                                      variable=self.hideonassignvar, onvalue=True, offvalue=False)
        hideonassign.grid(column=0, row=0)
        self.hidemovedvar = tk.BooleanVar()
        self.showhiddenvar = tk.BooleanVar()
        showhidden = tk.Checkbutton(optionsframe, text="Show Hidden Images",
                                    variable=self.showhiddenvar, onvalue=True, offvalue=False)
        showhidden.grid(column=0, row=1, sticky="W")
        hidemoved = tk.Checkbutton(optionsframe, text="Hide Moved",
                                   variable=self.hidemovedvar, onvalue=True, offvalue=False)
        hidemoved.grid(column=1, row=1)
        self.showhidden = showhidden
        self.hideonassign = hideonassign
        hideonassign.grid(column=1, row=0)
        moveallbutton = tk.Button(
            optionsframe, text="Move All", command=fileManager.moveall)
        moveallbutton.grid(column=0, row=2, columnspan=3, sticky="EW")

        self.optionsframe = optionsframe

    def showall(self):
        for x in self.fileManager.imagelist:
            if x.guidata["show"] == False:
                x.guidata["frame"].grid()
        self.hidemoved()
        self.hideassignedsquare(self.fileManager.imagelist)

    def closeprogram(self):
        saveprefs(self.fileManager, self)
        self.destroy()
        # shutil.rmtree("data",True)
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

    def makegridsquare(self, parent, imageobj):
        try:
            #buffer = pyvips.Image.new_from_file(imageobj.thumbnail)
            #img= ImageTk.PhotoImage(Image.frombuffer("L",[buffer.width,buffer.height],buffer.write_to_memory()))
            #Wish I knew how to make that work properly^
            img = ImageTk.PhotoImage(Image.open(imageobj.thumbnail))
            frame = tk.Frame(parent, width=self.thumbnailsize +
                             14, height=self.thumbnailsize+24)
            canvas = tk.Canvas(frame, width=self.thumbnailsize,
                               height=self.thumbnailsize)
            canvas.uuid = imageobj.id
            canvas.img = img
            canvas.create_image(
                self.thumbnailsize/2, self.thumbnailsize/2, anchor="center", image=img)

            text = textwrap.fill(
                imageobj.name, math.floor(self.thumbnailsize/12))
            check = Checkbutton(frame, text=text, variable=imageobj.checked)
            canvas.grid(column=0, row=0, sticky="NSEW")
            check.grid(column=0, row=1, sticky="N")
            frame.rowconfigure(0, weight=4)
            frame.rowconfigure(1, weight=1)
            frame.config(height=self.thumbnailsize+12)
            # save the data to the image obj to both store a reference and for later manipulation
            imageobj.setguidata(
                {"img": img, "frame": frame, "check": check, "show": True})
            # anything other than rightclicking toggles the checkbox, as we want.
            canvas.bind("<Button-1>", partial(bindhandler, check, "invoke"))
            canvas.bind(
                "<Button-3>", partial(self.displayimage, imageobj.path))
            check.bind("<Button-3>", partial(self.displayimage, imageobj.path))
            self.gridsquarelist.append(frame)
        except Exception as e:
            logging.error(e)

        return frame

    def displaygrid(self, imagelist, range):
        for i in range:
            gridsquare = self.makegridsquare(self.imagegrid, imagelist[i])
            self.imagegrid.window_create("insert", window=gridsquare)
            gridsquare.configure(height=self.thumbnailsize+10)
            gridsquare.bind_all("<MouseWheel>", partial(
                bindhandler, self.imagegrid, "scroll"))

    def buttonResizeOnWindowResize(self, b=""):
        if len(self.buttons) > 0:
            for x in self.buttons:
                x.configure(wraplength=(self.buttons[0].winfo_width()-1))

    def displayimage(self, path, a):
        logging.info("Displaying:" + path)
        imagewindow = tk.Toplevel()
        imagewindow.rowconfigure(0, weight=1)
        imagewindow.columnconfigure(0, weight=1)
        imagewindow.wm_title("Image: " + path)
        imagewindow.geometry(str(
            int(self.winfo_screenwidth()*0.80)) + "x" + str(self.winfo_screenheight()-120))
        imagewindow.geometry("+365+60")
        self.winfo_toplevel().title("SIS: " + path)
        imageframe = CanvasImage(imagewindow, path)
        # takes the smaller scale (since that will be the limiting factor) and rescales the image to that so it fits the frame.
        imageframe.rescale(min(imagewindow.winfo_width(
        )/imageframe.imwidth, imagewindow.winfo_height()/imageframe.imheight))
        imageframe.grid(column=0, row=0,)
        imagewindow.bind(
            "<Button-3>", partial(bindhandler, imagewindow, "destroy"))
        self.imagewindow = imagewindow

    def folderselect(self, _type):
        folder = tkFileDialog.askdirectory()
        if _type == "src":
            self.sdpEntry.delete(0, len(self.sdpEntry.get()))
            self.sdpEntry.insert(0, folder)
        if _type == "des":
            self.ddpEntry.delete(0, len(self.ddpEntry.get()))
            self.ddpEntry.insert(0, folder)

    def guisetup(self, destinations):
        panel = self.panel
        sdpEntry = self.sdpEntry
        ddpEntry = self.ddpEntry
        panel = self.panel
        buttonframe = self.buttonframe
        hotkeys = self.hotkeys
        for x in self.buttons:
            x.destroy()  # clear the gui
        panel.destroy()
        guirow = 1
        guicol = 0
        itern = 0
        smallfont = tkfont.Font(family='Helvetica', size=10)
        if len(destinations) > int((self.leftui.winfo_height()/15)-4):
            columns = 3
        for x in destinations:
            color = x['color']
            if x['name'] != "SKIP" and x['name'] != "BACK":
                if(itern < len(hotkeys)):
                    newbut = tk.Button(buttonframe, text=hotkeys[itern] + ": " + x['name'], command=partial(
                        self.fileManager.setDestination, x), anchor="w", wraplength=(self.leftui.winfo_width()/columns)-1)
                    random.seed(x['name'])
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
                        self.fileManager.setDestination, x), anchor="w")
                itern += 1
            newbut.config(font=("Courier", 12), width=int(
                (self.leftui.winfo_width()/12)/columns), height=1)
            if len(x['name']) > 20:
                newbut.config(font=smallfont)
            if guirow > ((self.leftui.winfo_height()/35)-2):
                guirow = 1
                guicol += 1
            x["color"] = color
            newbut.grid(row=guirow, column=guicol, sticky="nsew")
            newbut.bind("<Button-3>", partial(self.showthisdest, x))
            newbut.dest = x
            self.buttons.append(newbut)
            guirow += 1
        sdpEntry.config(state=tk.DISABLED)
        ddpEntry.config(state=tk.DISABLED)
        self.entryframe.grid_remove()
        self.optionsframe.grid(row=0, column=0, sticky="w")

    def hideassignedsquare(self, imlist):
        if self.hideonassignvar.get():
            for x in imlist:
                if x.dest != "":
                    x.guidata["frame"].grid_remove()
                    x.guidata["show"] = False

    def hideallsquares(self):
        for x in self.gridsquarelist:
            x.grid_remove()

    def showunassigned(self, imlist):
        for x in imlist:
            if x.guidata["show"] or x.dest == "":
                x.guidata["frame"].grid()
        self.hideassignedsquare(imlist)

    def showthisdest(self, dest):
        self.hideallsquares()
        for x in self.fileManager.imagelist:
            if x.dest == dest:
                x.guidata["frame"].grid()

    def hidemoved(self):
        if self.hidemovedvar.get():
            for x in self.fileManager.imagelist:
                if x.moved:
                    x.guidata["frame"].grid_remove()


class SortImages:
    imagelist = deque()
    destinations = []
    exclude = []
    thumbnailsize = 256

    def __init__(self) -> None:
        self.gui = GUIManager(self)
        # note, just load the preferences then pass it to the guimanager for processing there
        if(os.path.exists("data") and os.path.isdir("data")):
            pass
        else:
            os.mkdir(os.path.sep+"data")
        hotkeys = ""
        try:
            with open("prefs.json", "r") as prefsfile:
                jdata = prefsfile.read()
                jprefs = json.loads(jdata)
                if 'hotkeys' in jprefs:
                    hotkeys = jprefs["hotkeys"]
                if 'thumbnailgrid' in jprefs:
                    self.gui.thumbnailgrid = jprefs["thumbnailgrid"]
                if 'thumbnailsize' in jprefs:
                    self.gui.thumbnailsize = jprefs["thumbnailsize"]
                    self.thumbnailsize = jprefs["thumbnailsize"]
                if 'threads' in jprefs:
                    self.threads = jprefs['threads']
                else:
                    self.threads = 5
                self.exclude = jprefs["exclude"]
                self.gui.sdpEntry.delete(0, len(self.gui.sdpEntry.get()))
                self.gui.ddpEntry.delete(0, len(self.gui.ddpEntry.get()))
                self.gui.sdpEntry.insert(0, jprefs["srcpath"])
                self.gui.ddpEntry.insert(0, jprefs["despath"])
            if len(hotkeys) > 1:
                self.gui.hotkeys = hotkeys
        except Exception as e:
            logging.error(e)
        self.gui.mainloop()

    def moveall(self):
        loglist = []
        for x in self.imagelist:
            out = x.move()
            if isinstance(out, str):
                loglist.append(out)

        try:
            if len(loglist) > 0:
                with open("filelog.txt", "a") as logfile:
                    logfile.writelines(loglist)
        except:
            logging.error("Failed to write filelog.txt")
        self.gui.hidemoved()
            


    def walk(self, src):
        for root, dirs, files in os.walk(src, topdown=True):
            dirs[:] = [d for d in dirs if d not in self.exclude]
            for name in files:
                ext = name.split(".")[len(name.split("."))-1].lower()
                if ext == "png" or ext == "gif" or ext == "jpg" or ext == "jpeg" or ext == "bmp" or ext == "pcx" or ext == "tiff" or ext == "webp" or ext == "psd":
                    imgfile = Imagefile(name, os.path.join(root, name))
                    self.imagelist.append(imgfile)
        return self.imagelist

    def setDestination(self, dest):
        marked = []
        for x in self.imagelist:
            if x.checked.get() == 1:
                marked.append(x)
        for obj in marked:
            obj.setdest(dest)
            obj.guidata["frame"]['background'] = dest['color']
            obj.guidata["check"].invoke()
        self.gui.hideassignedsquare(marked)

    def validate(self, gui):
        samepath = (gui.sdpEntry.get() == gui.ddpEntry.get())
        if((os.path.isdir(gui.sdpEntry.get())) and (os.path.isdir(gui.ddpEntry.get())) and not samepath):
            self.sdp = gui.sdpEntry.get()
            self.ddp = gui.ddpEntry.get()
            logging.info("main class setup")
            self.setup(self.sdp, self.ddp)
            logging.info("GUI setup")
            gui.guisetup(self.destinations)
            logging.info("displaying first image grid")
            gui.displaygrid(self.imagelist, range(0, len(self.imagelist)))
        elif gui.sdpEntry.get() == gui.ddpEntry.get():
            gui.sdpEntry.delete(0, len(gui.sdpEntry.get()))
            gui.ddpEntry.delete(0, len(gui.ddpEntry.get()))
            gui.sdpEntry.insert(0, "PATHS CANNOT BE SAME")
            gui.ddpEntry.insert(0, "PATHS CANNOT BE SAME")
        else:
            gui.sdpEntry.delete(0, len(gui.sdpEntry.get()))
            gui.ddpEntry.delete(0, len(gui.ddpEntry.get()))
            gui.sdpEntry.insert(0, "ERROR INVALID PATH")
            gui.ddpEntry.insert(0, "ERROR INVALID PATH")

    def setup(self, src, dest):
        # scan the destination
        self.destinations = []
        with os.scandir(dest) as it:
            for entry in it:
                if entry.is_dir():
                    self.destinations.append(
                        {'name': entry.name, 'path': entry.path, 'color': randomColor()})
        self.generatethumbnails(self.walk(src))

    def makethumb(self, imagefile):
        im = pyvips.Image.new_from_file(imagefile.path,)
        hash = md5()
        hash.update(im.write_to_memory())
        imagefile.setid(hash.hexdigest())
        thumbpath = os.path.join("data", imagefile.id+os.extsep+"jpg")
        if os.path.exists(thumbpath):
            imagefile.thumbnail = thumbpath
        else:
            try:
                im = pyvips.Image.thumbnail(imagefile.path, self.thumbnailsize)
                im.write_to_file(thumbpath)
                imagefile.thumbnail = thumbpath
            except Exception as e:
                logging.error("Error:: %s", e)

    def generatethumbnails(self, images):
        logging.info("md5 hashing %s files", len(images))
        with concurrent.ThreadPoolExecutor(max_workers=self.threads) as executor:
            executor.map(self.makethumb, images)
        logging.info("Finished making thumbnails")


# Run Program
if __name__ == '__main__':
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
    mainclass = SortImages()
