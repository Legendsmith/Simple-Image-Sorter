import os
from sys import exit
import shutil
import tkinter as tk
import tkinter.scrolledtext as tkst
import PIL
from PIL import Image
from PIL import ImageTk
from functools import partial
from math import floor
import json
import atexit
import random
import math
from tkinter import filedialog as tkFileDialog
import tkinter.font as tkfont

#I am aware this code is fingerpaint-tier

tkroot = tk.Tk()
destinations = []
tkroot.geometry("360x900")
tkroot.geometry("+5+0")
buttons = []
imagelist=[]
imgiterator = 0
guirow=1
guicol=0
sdp=""
ddp=""
exclude=[]


#more guisetup
#######
#textout=tkst.ScrolledText(text_frame)
#textout.config(state=tk.DISABLED)

#def tklog(instring):
#replaced print but I can't get the positoning correct
	#global #textout
	#textout.config(state=tk.NORMAL)
	#textout.insert(tk.INSERT,"\n"+instring)
	#textout.config(state=tk.DISABLED)

def randomColor():
	color = '#'
	hexletters = '0123456789ABCDEF';
	for i in range(0,6):
		color += hexletters[math.floor(random.random()*16)]
	return color

def luminance(hexin):
	color = tuple(int(hexin.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
	r = color[0]
	g = color[1]
	b = color[2]
	hsp = math.sqrt(
		0.299 * (r**2) +
		0.587 * (g**2) +
		0.114 * (b**2)
		)
	if hsp >115.6:
		return 'light'
	else:
		return 'dark'



def validate():
	global sdp
	global ddp
	samepath =  (sdpEntry.get() == ddpEntry.get())
	if((os.path.isdir(sdpEntry.get())) and (os.path.isdir(ddpEntry.get())) and not samepath):
		sdp=sdpEntry.get()
		ddp=ddpEntry.get()
		setup(sdp,ddp)
		guisetup()
		displayimage()
	elif sdpEntry.get() == ddpEntry.get():
		sdpEntry.delete(0,len(sdpEntry.get()))
		ddpEntry.delete(0,len(ddpEntry.get()))
		sdpEntry.insert(0,"PATHS CANNOT BE SAME")
		ddpEntry.insert(0,"PATHS CANNOT BE SAME")
	else:
		sdpEntry.delete(0,len(sdpEntry.get()))
		ddpEntry.delete(0,len(ddpEntry.get()))
		sdpEntry.insert(0,"ERROR INVALID PATH")
		ddpEntry.insert(0,"ERROR INVALID PATH")


def setup(src,dest):
	global imagelist
	global destinations
	global imgiterator
	global exclude
	destinations = []
	imgiterator = 0
	#scan the destination
	if src[len(src)-1]=="\\":#trim trailing slashes
		src=src[:-1]
	if dest[len(dest)-1]=="\\":
		dest=dest[:-1]
	with os.scandir(dest) as it:
		for entry in it:
			if entry.is_dir():
				destinations.append({'name': entry.name,'path': entry.path})
		destinations.append({'name': "SKIP"})
	#walk the source files
	for root,dirs,files in os.walk(src,topdown=True):
		dirs[:] = [d for d in dirs if d not in exclude]
		for name in files:
			ext = name.split(".")[len(name.split("."))-1].lower()
			if ext == "png" or ext == "gif" or ext == "jpg" or ext == "jpeg" or ext == "bmp" or ext == "pcx" or ext == "tiff" or ext=="webp" or ext=="psd":
				imagelist.append({"name":name, "path":os.path.join(root,name)})



imagewindow = tk.Toplevel()
imagewindow.wm_title("Image")
imagewindow.geometry(str(int(tkroot.winfo_screenwidth()*0.75)) + "x"+ str(tkroot.winfo_screenheight()-100))
imagewindow.geometry("+370+0")
canvas=tk.Canvas(imagewindow)
canvas.pack(fill="both",expand=True)
framescroll=tk.Scrollbar(imagewindow)
framescroll.pack(side="right",expand="y")
canvas.config(width=1000,height=3000)
hotkeys = "123456qwerty7890uiop[asdfghjkl;zxcvbnm,.!@#$%^QWERT&*()_UIOPASDFGHJKLZXCVBNM<>"


panel = tk.Label(tkroot, wraplength=300, justify="left", text="""Select a source directory to search for images in above.
The program will find all png, gif, jpg, bmp, pcx, tiff, Webp, and psds. It can has as many sub-folders as you like, the program will scan them all (except exclusions).
Enter a root folder to sort to for the "Destination field" too. The destination directory MUST have sub folders, since those are the folders that you will be sorting to.
It is reccomended that the folder names are not more than say, 20 characters long. You can always rename them later if you desire longer names. Exclusions let you ignore folder names. They are saved (unless you delete prefs.json). Remember that it's one per line, no commas or anything.
You can change the hotkeys in prefs.json, just type a string of letters and numbers and it'll use that. It differentiates between lower and upper case (anything that uses shift), but not numpad.
Thanks for using this program!""")
##canvas.grid(row=1,column=2,columnspan=200,rowspan=200, sticky="NSEW")
panel.grid(row=11,column=0,columnspan=200,rowspan=200, sticky="NSEW")
framescroll.config(command=canvas.yview)
framescroll.pack(side="right",expand="y")
#panel.grid(row=1,column=guicol+1,columnspan=200,rowspan=200, sticky="NSEW")

tkroot.columnconfigure(0, weight=1)
buttonframe = tk.Frame(master=tkroot)
buttonframe.grid(column=0,row=2,sticky="NSEW",rowspan=2,columnspan=3,)
buttonframe.columnconfigure(0,weight=1)
buttonframe.columnconfigure(1,weight=1)
buttonframe.columnconfigure(2,weight=1)



def movefile(dest,event=None):
	global imgiterator
	shutil.move(imagelist[imgiterator]["path"],dest+"\\"+imagelist[imgiterator]["name"])
	print("Moved: " + imagelist[imgiterator]["name"] + " to " +dest)
	imgiterator+=1
	displayimage()


def skip(event=None):
	global imgiterator
	imgiterator+=1
	displayimage()

def guisetup():
	global guicol
	global guirow
	global panel
	global sdpEntry
	global ddpEntry
	global canvas
	global panel
	global framescroll
	global buttonframe
	global hotkeys
	for x in buttons:
		x.destroy() #clear the gui
	panel.destroy()
	guirow=1
	guicol=0
	itern=0
	smallfont = tkfont.Font( family='Helvetica',size=10)
	for x in destinations:
		if x['name'] is not "SKIP":
			if(itern < len(hotkeys)):
				newbut = tk.Button(buttonframe, text=hotkeys[itern] +": "+ x['name'], command= partial(movefile,x['path']),anchor="w", wraplength=tkroot.winfo_width()/2)
				random.seed(x['name'])
				tkroot.bind(hotkeys[itern],partial(movefile,x['path']))
				color = randomColor()
				fg = 'white'

				if luminance(color) == 'light':
					fg = "black"
				newbut.configure(bg =color, fg =fg)
				if(len(x['name'])>=13):
					newbut.configure(font=smallfont)

			else:
				newbut = tk.Button(buttonframe, text=x['name'], command= partial(movefile,x['path']),anchor="w")
			itern+=1
		elif x['name'] == "SKIP":
			newbut = tk.Button(buttonframe, text="SKIP (Space)", command=skip)
			tkroot.bind("<space>",skip)
		newbut.config(font=("Courier",12),width=17,height=1)
		if guirow-2==int(floor(len(destinations))/2):
			guirow=1
			guicol+=1
		newbut.grid(row=guirow,column=guicol,sticky="ew")
		buttons.append(newbut)
		guirow+=1
		
	#textout.grid(column=0,row=0, sticky="nsew")
	sdpEntry.config(state=tk.DISABLED)
	ddpEntry.config(state=tk.DISABLED)
	

def displayimage():
	global imgiterator
	global panel
	global guicol
	global canvas
	#if imgiterator>len(imagelist):
	print("Displaying:"+ imagelist[imgiterator]['path'])
	tkroot.winfo_toplevel().title("Simple Image Sorter: " +imagelist[imgiterator]['path'])
	imagewindow.wm_title(imagelist[imgiterator]['path'])
	img = Image.open(imagelist[imgiterator]['path'])
	img.thumbnail([imagewindow.winfo_screenwidth(),imagewindow.winfo_height()],PIL.Image.ANTIALIAS)
	img = ImageTk.PhotoImage(img)
	#panel.config(image=img)
	canvas.img=img
	canvas.create_image(0, 0, image=img, anchor="nw")
	#panel.grid(row=1,column=guicol+1,columnspan=200,rowspan=200, sticky="NSEW")
	#else:
	#	panel=tk.Label(tkroot,text="NO MORE IMAGES")
	#	panel.grid(row=0,column=2)


def folderselect(_type):
	folder = tkFileDialog.askdirectory()
	if _type == "src":
		sdpEntry.delete(0,len(sdpEntry.get()))
		sdpEntry.insert(0,folder)
	if _type == "des":
		ddpEntry.delete(0,len(ddpEntry.get()))
		ddpEntry.insert(0,folder)

def saveonexit():
	global sdp
	global ddp
	save={"srcpath":sdp, "despath":ddp,"exclude":exclude, "hotkeys":hotkeys}
	try:
		with open("prefs.json", "w+") as savef:
			json.dump(save,savef)
	except Exception:
		pass
atexit.register(saveonexit)
#gui setup
sdpEntry = tk.Entry(tkroot) #scandirpathEntry
ddpEntry= tk.Entry(tkroot)#dest dir path entry

sdplabel= tk.Button(tkroot,text="Source Folder:", command=partial(folderselect,"src"))
ddplabel= tk.Button(tkroot,text="Destination Folder:", command=partial(folderselect,"des" ))
activebutton=tk.Button(tkroot,text="Ready",command=validate)

sdplabel.grid(row=0,column=0,sticky="e")
sdpEntry.grid(row=0,column=1,sticky="w")
ddplabel.grid(row=1,column=0,sticky="e")
ddpEntry.grid(row=1,column=1,sticky="w")
activebutton.grid(row=1,column=2,sticky="ew")

def excludeshow():
	global exclude
	excludewindow = tk.Toplevel()
	excludewindow.winfo_toplevel().title("Folder names to ignore, one per line. This will ignore sub-folders too.")
	excludetext=tkst.ScrolledText(excludewindow)
	for x in exclude:
		excludetext.insert("1.0",x+"\n")
	excludetext.pack()
	excludewindow.protocol("WM_DELETE_WINDOW",partial(excludesave,text=excludetext,toplevelwin=excludewindow))

excludebutton=tk.Button(tkroot,text="Manage Exclusions",command=excludeshow)
excludebutton.grid(row=0,column=2)

def excludesave(text,toplevelwin):
	global exclude
	text= text.get('1.0', tk.END).splitlines()
	exclude=[]
	for line in text:
		exclude.append(line)
	print("List of excluded folder names:")
	print(exclude)
	try:
		toplevelwin.destroy()
	except:
		pass
#INITIATE
try:
	with open("prefs.json","r") as prefsfile:
		jdata=prefsfile.read()
		jprefs=json.loads(jdata)
		print(jprefs)
		sdpEntry.delete(0,len(sdpEntry.get()))
		ddpEntry.delete(0,len(ddpEntry.get()))
		sdpEntry.insert(0,jprefs["srcpath"])
		ddpEntry.insert(0,jprefs["despath"])
		if 'hotkeys' in jprefs:
			hotkeys = jprefs["hotkeys"]
		exclude=jprefs["exclude"]
	if hotkeys=="":
		hotkeys="123456qwerty7890uiop[asdfghjkl;zxcvbnm,.!@#$%^QWERT&*()_UIOPASDFGHJKLZXCVBNM<>"
except Exception:
	pass
#textout.config(state=tk.DISABLED)
#textout.insert(tk.INSERT,"""No images Loaded yet.
#Enter a source directory in the relevant text field. It can has as many sub-folders as you like, the program will scan them all.
#Enter a root folder to sort to for the "Destination field" too.
#Both of these must have valid paths. That is, they are folders that actually exist.
#The destination directory MUST have sub folders, since those are the folders that you will be sorting to. It is reccomended that the folder names are not more than say, 20 characters long.
#You can always rename them later if you desire longer names.
#Thanks for using this program!""")
#textout.config(state=tk.DISABLED)
tkroot.winfo_toplevel().title("Simple Image Sorter v0.9")


def buttonResizeOnWindowResize(x):
	if len(buttons)>0:
		for x in buttons:
			x.configure(wraplength=tkroot.winfo_width()/2)
tkroot.bind("<Configure>", buttonResizeOnWindowResize)

tkroot.mainloop()
