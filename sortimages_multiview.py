# todo:
# Filename dupicate scanning to prevent collisions
# Check if filename already exists on move.
# implement undo
import os
from sys import exit
from shutil import move as shmove
import tkinter as tk
from tkinter.messagebox import askokcancel
from math import floor
import json
import random
from math import floor, sqrt
from tkinter import filedialog as tkFileDialog
import concurrent.futures as concurrent
import logging
from hashlib import md5
import pyvips
from gui import GUIManager, randomColor

class Imagefile:
    path = ""
    dest = ""
    dupename=False

    def __init__(self, name, path) -> None:
        self.name = tk.StringVar()
        self.name.set(name)
        self.path = path
        self.checked = tk.BooleanVar(value=False)
        self.moved = False

    def move(self) -> str:
        destpath = self.dest

        if destpath != "" and os.path.isdir(destpath):
            file_name = self.name.get()

            # Check for name conflicts (source -> destination)
            exists_already_in_destination = os.path.exists(os.path.join(destpath, file_name))
            if exists_already_in_destination:
                print(f"File {self.name.get()[:30]} already exists at destination. Cancelling move.")
                return ("") # Returns if 1. Would overwrite someone
            
            try:
                new_path = os.path.join(destpath, file_name)
                old_path = self.path

                # Throws exception when image is open.
                shmove(self.path, new_path)

                self.moved = True
                self.show = False

                self.guidata["frame"].configure(
                    highlightbackground="green", highlightthickness=2)

                self.path = new_path
                returnstr = ("Moved:" + self.name.get() +
                             " -> " + destpath + "\n")
                destpath = ""
                self.dest = ""
                self.hasunmoved = False
                return returnstr
            except Exception as e:
                # Shutil failed. Delete the copy from destination, leaving the original at source.
                # This only runs if shutil fails, meaning the image couldn't be deleted from source.
                # It is therefore safe to delete the destination copy.
                if os.path.exists(new_path) and os.path.exists(old_path):
                    os.remove(new_path)
                    print("Shutil failed. Coudln't delete from source, cancelling move (deleting copy from destination)")
                    return "Shutil failed. Coudln't delete from source, cancelling move (deleting copy from destination)"
                else:
                    logging.warning(f"Error moving/deleting: %s . File: %s {e} {self.name.get()}")

                self.guidata["frame"].configure(
                    highlightbackground="red", highlightthickness=2)
                return ("Error moving: %s . File: %s", e, self.name.get())

    def setid(self, id):
        self.id = id

    def setguidata(self, data):
        self.guidata = data

    def setdest(self, dest):
        self.dest = dest["path"]
        logging.debug("Set destination of %s to %s",
                      self.name.get(), self.dest)


class SortImages:
    imagelist = []
    destinations = []
    exclude = []
    thumbnailsize = 256

    def __init__(self) -> None:
        self.hasunmoved=False
        self.existingnames = set()
        self.duplicatenames=[]
        self.autosave=True
        self.gui = GUIManager(self)
        # note, just load the preferences then pass it to the guimanager for processing there
        if(os.path.exists("data") and os.path.isdir("data")):
            pass
        else:
            os.mkdir("data")
        hotkeys = ""
        # todo: replace this with some actual prefs manager that isn't a shittone of ifs
        self.threads = 5
        try:
            with open("prefs.json", "r") as prefsfile:
                jdata = prefsfile.read()
                jprefs = json.loads(jdata)
                if 'hotkeys' in jprefs:
                    hotkeys = jprefs["hotkeys"]
                if 'thumbnailsize' in jprefs:
                    self.gui.thumbnailsize = int(jprefs["thumbnailsize"])
                    self.thumbnailsize = int(jprefs["thumbnailsize"])
                if 'threads' in jprefs:
                    self.threads = jprefs['threads']
                if "hideonassign" in jprefs:
                    self.gui.hideonassignvar.set(jprefs["hideonassign"])
                if "hidemoved" in jprefs:
                    self.gui.hidemovedvar.set(jprefs["hidemoved"])
                if "sortbydate" in jprefs:
                   self.gui.sortbydatevar.set(jprefs["sortbydate"])
                self.exclude = jprefs["exclude"]
                self.gui.sdpEntry.delete(0, len(self.gui.sdpEntry.get()))
                self.gui.ddpEntry.delete(0, len(self.gui.ddpEntry.get()))
                self.gui.sdpEntry.insert(0, jprefs["srcpath"])
                self.gui.ddpEntry.insert(0, jprefs["despath"])
                if "squaresperpage" in jprefs:
                    self.gui.squaresperpage.set(int(jprefs["squaresperpage"]))
                if "geometry" in jprefs:
                    self.gui.geometry(jprefs["geometry"])
                if "lastsession" in jprefs:
                    self.gui.sessionpathvar.set(jprefs['lastsession'])
                if "autosavesession" in jprefs:
                    self.autosave = jprefs['autosave']
            if len(hotkeys) > 1:
                self.gui.hotkeys = hotkeys
        except Exception as e:
            logging.error("Error loading prefs.json, it is possibly corrupt, try deleting it, or else it doesn't exist and will be created upon exiting the program.")
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
        except Exception as e:
            logging.error(f"Failed to write filelog.txt: {e}")
        self.gui.hidemoved()

    def walk(self, src):
        duplicates = self.duplicatenames
        existing = self.existingnames
        for root, dirs, files in os.walk(src, topdown=True):
            dirs[:] = [d for d in dirs if d not in self.exclude]
            for name in files:
                ext = name.split(".")[len(name.split("."))-1].lower()
                if ext == "png" or ext == "gif" or ext == "jpg" or ext == "jpeg" or ext == "bmp" or ext == "pcx" or ext == "tiff" or ext == "webp" or ext == "psd":
                    imgfile = Imagefile(name, os.path.join(root, name))
                    if name in existing:
                        duplicates.append(imgfile)
                        imgfile.dupename=True
                    else:
                        existing.add(name)
                    self.imagelist.append(imgfile)

        #Default sorting is based on name. This sorts by date modified.
        if self.gui.sortbydatevar.get():
            self.imagelist.sort(key=lambda img: os.path.getmtime(img.path), reverse=True)

        return self.imagelist
            
                
    def checkdupefilenames(self, imagelist):
        duplicates: list[Imagefile] = []
        existing: set[str] = set()

        for item in imagelist:
            if item.name.get() in existing:
                duplicates.append(item)
                item.dupename=True
            else:
                existing.add(item.name)
        return duplicates
        
    def setDestination(self, *args):
        self.hasunmoved = True
        marked = []
        dest = args[0]
        try:
            wid = args[1].widget
        except AttributeError:
            wid = args[1]["widget"]
        if isinstance(wid, tk.Entry):
            pass
        else:
            for x in self.imagelist:
                if x.checked.get():
                    marked.append(x)
            for obj in marked:
                obj.setdest(dest)
                obj.guidata["frame"]['background'] = dest['color']
                obj.guidata["canvas"]['background'] = dest['color']
                obj.checked.set(False)
            self.gui.hideassignedsquare(marked)

    def savesession(self,asksavelocation):
        if asksavelocation:
            filet=[("Javascript Object Notation","*.json")]
            savelocation=tkFileDialog.asksaveasfilename(confirmoverwrite=True,defaultextension=filet,filetypes=filet,initialdir=os.getcwd(),initialfile=self.gui.sessionpathvar.get())
        else:
            savelocation = self.gui.sessionpathvar.get()
        if len(self.imagelist) > 0:
            imagesavedata = []
            for obj in self.imagelist:
                if hasattr(obj, 'thumbnail'):
                    thumb = obj.thumbnail
                else:
                    thumb = ""
                imagesavedata.append({
                    "name": obj.name.get(),
                    "path": obj.path,
                    "dest": obj.dest,
                    "checked": obj.checked.get(),
                    "moved": obj.moved,
                    "thumbnail": thumb,
                    "dupename":obj.dupename
                })
            save = {"dest": self.ddp, "source": self.sdp,
                    "imagelist": imagesavedata,"thumbnailsize":self.thumbnailsize,'existingnames':list(self.existingnames)}
            with open(savelocation, "w+") as savef:
                json.dump(save, savef)

    def loadsession(self):
        sessionpath = self.gui.sessionpathvar.get()
        if os.path.exists(sessionpath) and os.path.isfile(sessionpath):
            with open(sessionpath, "r") as savef:
                sdata = savef.read()
                savedata = json.loads(sdata)
            gui = self.gui
            self.ddp = savedata['dest']
            self.sdp = savedata['source']
            self.setup(savedata['dest'])
            if 'existingnames' in savedata:
                self.existingnames = set(savedata['existingnames'])
            for o in savedata['imagelist']:
                if os.path.exists(o['path']):
                    n = Imagefile(o['name'], o['path'])
                    n.checked.set(o['checked'])
                    n.moved = o['moved']
                    n.thumbnail = o['thumbnail']
                    n.dupename=o['dupename']
                    n.dest=o['dest']
                    self.imagelist.append(n)
            self.thumbnailsize=savedata['thumbnailsize']
            self.gui.thumbnailsize=savedata['thumbnailsize']
            listmax = min(gui.squaresperpage.get(), len(self.imagelist))
            sublist = self.imagelist[0:listmax]
            gui.displaygrid(self.imagelist, range(0, min(gui.squaresperpage.get(),listmax)))
            gui.guisetup(self.destinations)
            gui.hidemoved()
            gui.hideassignedsquare(sublist)
        else:
            logging.error("No Last Session!")

    def validate(self, gui):
        samepath = (gui.sdpEntry.get() == gui.ddpEntry.get())
        if((os.path.isdir(gui.sdpEntry.get())) and (os.path.isdir(gui.ddpEntry.get())) and not samepath):
            self.sdp = gui.sdpEntry.get()
            self.ddp = gui.ddpEntry.get()
            logging.info("main class setup")
            self.setup(self.ddp)
            logging.info("GUI setup")
            gui.guisetup(self.destinations)
            gui.sessionpathvar.set(os.path.basename(
                self.sdp)+"-"+os.path.basename(self.ddp)+".json")
            logging.info("displaying first image grid")
            self.walk(self.sdp)
            listmax = min(gui.squaresperpage.get(), len(self.imagelist))
            sublist = self.imagelist[0:listmax]
            self.generatethumbnails(sublist)
            gui.displaygrid(self.imagelist, range(0, min(len(self.imagelist), gui.squaresperpage.get())))
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

    def setup(self, dest):
        # scan the destination
        self.destinations = []
        self.destinationsraw = []
        with os.scandir(dest) as it:
            for entry in it:
                if entry.is_dir():
                    random.seed(entry.name)
                    self.destinations.append(
                        {'name': entry.name, 'path': entry.path, 'color': randomColor()})
                    self.destinationsraw.append(entry.path)

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

    def clear(self, *args):
        if askokcancel("Confirm", "Really clear your selection?"):
            for x in self.imagelist:
                x.checked.set(False)


# Run Program
if __name__ == '__main__':
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(
        format=format, level=logging.WARNING, datefmt="%H:%M:%S")
    mainclass = SortImages()
