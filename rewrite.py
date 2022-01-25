import os
import shutil
from sys import exit
from tkinter import HORIZONTAL, RAISED, PhotoImage, messagebox
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
import uuid
import logging
from autoscrollbar import AutoScrollbar

class Imagefile:
    name=""
    path=""
    dest=""
    moved=False
    def __init__(self,name,path) -> None:
        self.name=name
        self.path=path
        self.id=str(uuid.uuid1())
        self.checked=tk.StringVar()
    def move(self):
        if self.dest != "":
            try:
                shmove(self.path, os.path.join(self.dest,self.name))
                self.moved=True
            except Exception as e:
                logging.error("Error: %s . File: %s",e,self.name)

    

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


def saveprefs(manager,gui):
    if os.path.exists(gui.sdpEntry.get()):
        sdp = gui.sdpEntry.get()
    else:
        sdp = ""
    if os.path.exists(gui.ddpEntry.get()):
        ddp = gui.ddpEntry.get()
    else:
        ddp=""
    save={"srcpath":sdp, "despath":ddp,"exclude":manager.exclude, "hotkeys":gui.hotkeys,"thumbnailgrid":gui.thumbnailgrid,"thumbnailsize":gui.thumbnailsize}
    try:
        with open("prefs.json", "w+") as savef:
            json.dump(save,savef)
            logging.debug(save)
    except Exception:
        pass



class GUIManager(tk.Tk):
    thumbnailgrid=[3,3]
    thumbnailsize=256
    def __init__(self, fileManager) -> None:
        super().__init__()
        self.fileManager=fileManager
        self.geometry(str(self.winfo_screenwidth()-5)+"x"+str(self.winfo_screenheight()-120))
        self.geometry("+0+60")
        self.buttons = []
        self.hotkeys = "123456qwerty7890uiop[asdfghjkl;zxcvbnm,.!@#$%^QWERT&*()_UIOPASDFGHJKLZXCVBNM<>"
        #Paned window that holds the almost top level stuff.
        self.toppane= Panedwindow(self,orient=HORIZONTAL)
        # Frame for the left hand side that holds the setup and also the destination buttons.
        self.leftui=tk.Frame(self.toppane)
        self.leftui.grid(row=0,column=0,sticky="NESW")
        self.leftui.columnconfigure(0,weight=1)
        self.leftui.columnconfigure(1,weight=1)
        self.leftui.columnconfigure(2,weight=1)
        self.toppane.add(self.leftui,weight=1)
        self.panel = tk.Label(self.leftui, wraplength=300, justify="left", text="""Select a source directory to search for images in above.
The program will find all png, gif, jpg, bmp, pcx, tiff, Webp, and psds. It can has as many sub-folders as you like, the program will scan them all (except exclusions).
Enter a root folder to sort to for the "Destination field" too. The destination directory MUST have sub folders, since those are the folders that you will be sorting to.
It is reccomended that the folder names are not super long. You can always rename them later if you desire longer names. Exclusions let you ignore folder names. They are saved (unless you delete prefs.json). Remember that it's one per line, no commas or anything.
You can change the hotkeys in prefs.json, just type a string of letters and numbers and it'll use that. It differentiates between lower and upper case (anything that uses shift), but not numpad.
Thanks to FooBar167 on stackoverflow for the advanced (and memory efficient!) Zoom and Pan tkinter class.
You can use arrow keys or click and drag to pan the image. Mouse Wheel Zooms the image.
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
        self.entryframe=tk.Frame(master=self.leftui)
        self.sdpEntry = tk.Entry(self.entryframe)  # scandirpathEntry
        self.ddpEntry = tk.Entry(self.entryframe)  # dest dir path entry

        self.sdplabel = tk.Button(
            self.entryframe, text="Source Folder:", command=partial(self.folderselect, "src"))
        self.ddplabel = tk.Button(
            self.entryframe, text="Destination Folder:", command=partial(self.folderselect, "des"))
        self.activebutton = tk.Button(self.entryframe, text="Ready", command=partial(fileManager.validate,self))

        self.sdplabel.grid(row=0,column=0,sticky="e")
        self.sdpEntry.grid(row=0,column=1,sticky="w")
        self.ddplabel.grid(row=1,column=0,sticky="e")
        self.ddpEntry.grid(row=1,column=1,sticky="w")
        self.activebutton.grid(row=1, column=2, sticky="ew")
        self.excludebutton=tk.Button(self.entryframe,text="Manage Exclusions",command=self.excludeshow)
        self.excludebutton.grid(row=0,column=2)
        #show the entry frame, sticky it to the west so it mostly stays put.
        self.entryframe.grid(row=0,column=0,sticky="w")
        #Finish setup for the left hand bar.
        #Start the grid setup
        imagegridframe = tk.Frame(self.toppane)
        imagegridframe.grid(row=0,column=1,sticky="NSEW")
        vbar =AutoScrollbar(imagegridframe,orient='vertical')
        vbar.grid(row=0, column=1, sticky='ns')
        self.imagegrid=tk.Text(imagegridframe,wrap='char',borderwidth=0,highlightthickness=0,state="disabled")
        self.imagegrid['background']='#a9a9a9' # set background color to a darker grey
        self.imagegrid.grid(row=0,column=0,sticky="NSEW")
        imagegridframe.rowconfigure(0, weight=1) 
        imagegridframe.columnconfigure(0, weight=1)

        self.toppane.add(imagegridframe,weight=3)
        self.toppane.grid(row=0,column=0,columnspan=200,rowspan=200,sticky="NSEW")
        self.toppane.configure()
        self.columnconfigure(0,weight=10)
        self.columnconfigure(1,weight=0)
        self.rowconfigure(0,weight=10)
        self.rowconfigure(1,weight=0)
        self.protocol("WM_DELETE_WINDOW", self.closeprogram)
        self.winfo_toplevel().title("Simple Image Sorter v2.0")
        self.leftui.bind("<Configure>", self.buttonResizeOnWindowResize)
        self.buttonResizeOnWindowResize("a")
    def closeprogram(self):
        saveprefs(self.fileManager, self)
        self.destroy()
        shutil.rmtree("data",True)
        exit(0)
    def excludeshow(self):
        excludewindow = tk.Toplevel()
        excludewindow.winfo_toplevel().title("Folder names to ignore, one per line. This will ignore sub-folders too.")
        excludetext=tkst.ScrolledText(excludewindow)
        for x in self.fileManager.exclude:
            excludetext.insert("1.0",x+"\n")
        excludetext.pack()
        excludewindow.protocol("WM_DELETE_WINDOW",partial(self.excludesave,text=excludetext,toplevelwin=excludewindow))      
    def excludesave(self,text,toplevelwin):
        text= text.get('1.0', tk.END).splitlines()
        exclude=[]
        for line in text:
            exclude.append(line)
        self.fileManager.exclude=exclude
        try:
            toplevelwin.destroy()
        except:
            pass
    def makegridsquare(self,parent,imageobj):
        frame = tk.Frame(parent,relief=RAISED,width=self.thumbnailsize)
        try: 
            frame.uuid=imageobj.id
            canvas = tk.Canvas(width=self.thumbnailsize,height=self.thumbnailsize)
            img= PhotoImage(imageobj.thumbnail)
            canvas.create_image(self.thumbnailsize,self.thumbnailsize,image=img,anchor="nw")
            canvas.grid(column=0,row=0,sticky="NSEW")
            check=Checkbutton(frame, text=imageobj.name,variable=imageobj.checked)
            check.grid(column=0,row=1)
            canvas.imagetk=img
            canvas.bind("<Button-2>", partial(self.displayimage,imageobj.path))
            frame.bind("<Button-1>",check.invoke()) #anything other than rightclicking toggles the checkbox, as we want.
            canvas.bind("<Button-1>",check.invoke())
        except Exception as e:
            logging.error(e)

        return frame
    def displaygrid(self,imagelist,range):
        for i in range:
            logging.debug(i)
            gridsqaure = self.makegridsquare(self.imagegrid,imagelist[i])
            gridsqaure.grid(row=0,column=0, ipadx=4,ipady=4)



    def buttonResizeOnWindowResize(self, b=""):
        if len(self.buttons) > 0:
            for x in self.buttons:
                x.configure(wraplength=(self.buttons[0].winfo_width()-1))
    def displayimage(self, path):
        logging.INFO("Displaying:" + path)
        self.imagewindow = tk.Toplevel()
        self.imagewindow.rowconfigure(0, weight=1)
        self.imagewindow.columnconfigure(0, weight=1)
        self.imagewindow.wm_title("Image: "+ path)
        self.imagewindow.geometry(str(
            int(self.winfo_screenwidth()*0.80)) + "x" + str(self.winfo_screenheight()-120))
        self.imagewindow.geometry("+365+60")
        self.winfo_toplevel().title("SIS: " + path)
        imageframe = CanvasImage(self.imagewindow, path)
        # takes the smaller scale (since that will be the limiting factor) and rescales the image to that so it fits the frame.
        imageframe.rescale(min(self.imagewindow.winfo_width(
        )/imageframe.imwidth, self.imagewindow.winfo_height()/imageframe.imheight))
        imageframe.grid(column=0, row=0,)

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
            if x['name'] != "SKIP" and x['name'] != "BACK":
                if(itern < len(hotkeys)):
                    newbut = tk.Button(buttonframe, text=hotkeys[itern] + ": " + x['name'], command=partial(
                        self.fileManager.setDestination, x['path']), anchor="w", wraplength=(self.leftui.winfo_width()/columns)-1)
                    random.seed(x['name'])
                    self.bind_all(hotkeys[itern], partial(self.fileManager.setDestination, x['path']))
                    color = randomColor()
                    fg = 'white'

                    if luminance(color) == 'light':
                        fg = "black"
                    newbut.configure(bg=color, fg=fg)
                    if(len(x['name']) >= 13):
                        newbut.configure(font=smallfont)
                else:
                    newbut = tk.Button(buttonframe, text=x['name'], command=partial(
                        self.fileManager.setDestination, x['path']), anchor="w")
                itern += 1
            newbut.config(font=("Courier", 12), width=int(
                (self.leftui.winfo_width()/12)/columns), height=1)
            if len(x['name']) > 20:
                newbut.config(font=smallfont)
            if guirow > ((self.leftui.winfo_height()/35)-2):
                guirow = 1
                guicol += 1
            newbut.grid(row=guirow, column=guicol, sticky="nsew")
            self.buttons.append(newbut)
            guirow += 1

        #textout.grid(column=0,row=0, sticky="nsew")
        sdpEntry.config(state=tk.DISABLED)
        ddpEntry.config(state=tk.DISABLED)
        # zoom


class SortImages:
    imagelist = deque()
    destinations=[]
    exclude=[]
    thumbnailsize=256
    def __init__(self) -> None:
        self.gui = GUIManager(self)
        if(os.path.exists("data") and os.path.isdir("data")):
            pass
        else:
            os.mkdir(os.path.sep+"data")
        hotkeys = ""
        try:
            with open("prefs.json","r") as prefsfile:
                jdata=prefsfile.read()
                jprefs=json.loads(jdata)
                if 'hotkeys' in jprefs:
                    hotkeys = jprefs["hotkeys"]
                if 'thumbnailgrid' in jprefs:
                    self.gui.thumbnailgrid = jprefs["thumbnailgrid"]
                if 'thumbnailsize' in jprefs:
                    self.gui.thumbnailsize = jprefs["thumbnailsize"]
                    self.thumbnailsize = jprefs["thumbnailsize"]
                self.exclude = jprefs["exclude"]
                self.gui.sdpEntry.delete(0,len(self.gui.sdpEntry.get()))
                self.gui.ddpEntry.delete(0,len(self.gui.ddpEntry.get()))
                self.gui.sdpEntry.insert(0,jprefs["srcpath"])
                self.gui.ddpEntry.insert(0,jprefs["despath"])
            if len(hotkeys) > 1:
                    self.gui.hotkeys=hotkeys
        except Exception as e:
            logging.error(e)
        self.gui.mainloop()
        

    def walk(self,src):
        for root,dirs,files in os.walk(src,topdown=True):
            dirs[:] = [d for d in dirs if d not in self.exclude]
            for name in files:
                ext = name.split(".")[len(name.split("."))-1].lower()
                if ext == "png" or ext == "gif" or ext == "jpg" or ext == "jpeg" or ext == "bmp" or ext == "pcx" or ext == "tiff" or ext=="webp" or ext=="psd" or ext=="jfif":
                    imgfile = Imagefile(name, os.path.join(root,name))
                    self.imagelist.append(imgfile)
        return self.imagelist
    def setDestination(self,dest):
        pass
    def validate(self,gui):
        samepath =  (gui.sdpEntry.get() == gui.ddpEntry.get())
        if((os.path.isdir(gui.sdpEntry.get())) and (os.path.isdir(gui.ddpEntry.get())) and not samepath):
            self.sdp=gui.sdpEntry.get()
            self.ddp=gui.ddpEntry.get()
            self.setup(self.sdp,self.ddp)
            gui.guisetup(self.destinations)
            gui.displaygrid(self.imagelist,range(0,10))
        elif gui.sdpEntry.get() == gui.ddpEntry.get():
            gui.sdpEntry.delete(0,len(gui.sdpEntry.get()))
            gui.ddpEntry.delete(0,len(gui.ddpEntry.get()))
            gui.sdpEntry.insert(0,"PATHS CANNOT BE SAME")
            gui.ddpEntry.insert(0,"PATHS CANNOT BE SAME")
        else:
            gui.sdpEntry.delete(0,len(gui.sdpEntry.get()))
            gui.ddpEntry.delete(0,len(gui.ddpEntry.get()))
            gui.sdpEntry.insert(0,"ERROR INVALID PATH")
            gui.ddpEntry.insert(0,"ERROR INVALID PATH")
    def setup(self,src,dest):
        #scan the destination
        self.destinations=[]
        with os.scandir(dest) as it:
            for entry in it:
                if entry.is_dir():
                    self.destinations.append({'name': entry.name,'path': entry.path})
        self.generatethumbnails(self.walk(src))

    def makethumb(self,imagefile):
        try:
            thumbsize=self.thumbnailsize
            im = Image.open(imagefile.path)
            if im.mode in ("RGBA", "P"): im = im.convert("RGB") #discard transparency
            MAX_SIZE=(thumbsize,thumbsize)
            im.thumbnail(MAX_SIZE)
            thumbpath=os.path.join("data",imagefile.id+os.extsep+"jpg")
            im.save(thumbpath)
            imagefile.thumbnail=thumbpath
        except Exception as e:
            logging.error("Error:: %s",e)
    def generatethumbnails(self,images):
        with concurrent.ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(self.makethumb, images)
        logging.debug("Finished making thumbnails")



# Run Program
if __name__ == '__main__':
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG,datefmt="%H:%M:%S")
    mainclass = SortImages()