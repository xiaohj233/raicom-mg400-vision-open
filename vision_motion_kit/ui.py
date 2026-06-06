from __future__ import annotations
import queue, threading, tkinter as tk
from pathlib import Path
from tkinter.scrolledtext import ScrolledText
from .transport import listen_in_thread
try:
    from PIL import Image, ImageTk
except Exception:
    Image=ImageTk=None

def start_thread(fn, log=None, err_text='ERR:'):
    def run():
        try: fn()
        except Exception as e:
            (log or print)(str(err_text)+str(e))
    threading.Thread(target=run,daemon=True).start()

def tk_logger(root, box):
    q=queue.Queue()
    def flush():
        while True:
            try: s=q.get_nowait()
            except queue.Empty: break
            box.insert('end',str(s)+'\n'); box.see('end')
        root.after(80, flush)
    root.after(80, flush)
    return lambda s:q.put(str(s))

class ControlPanel:
    def __init__(self, title=None, text=None):
        self.text={
            'title':'RAICOM',
            'robot_frame':'Robot',
            'vision_frame':'Vision',
            'monitor_frame':'Monitor',
            'new_photo':'waiting new photo...',
            'missing_image':'image missing/waiting',
        }
        if text: self.text.update(text)
        self.root=tk.Tk(); self.root.title(title or self.text['title']); self.root.geometry('1280x720')
        self.root.grid_columnconfigure(1,weight=1); self.root.grid_columnconfigure(2,weight=1); self.root.grid_rowconfigure(0,weight=1)
        self.robot=tk.LabelFrame(self.root,text=self.text['robot_frame']); self.robot.grid(row=0,column=0,sticky='ns',padx=6,pady=6)
        self.vision=tk.LabelFrame(self.root,text=self.text['vision_frame']); self.vision.grid(row=0,column=1,sticky='nsew',padx=6,pady=6)
        self.vision.grid_rowconfigure(0,weight=1,minsize=540); self.vision.grid_columnconfigure(0,weight=1,minsize=720)
        self.monf=tk.LabelFrame(self.root,text=self.text['monitor_frame']); self.monf.grid(row=0,column=2,sticky='nsew',padx=6,pady=6)
        self.monf.grid_rowconfigure(0,weight=1); self.monf.grid_columnconfigure(0,weight=1)
        self.canvas=tk.Canvas(self.vision,bg='#eee',width=720,height=540); self.canvas.grid(row=0,column=0,sticky='nsew')
        self.mon=ScrolledText(self.monf,width=52); self.mon.grid(row=0,column=0,sticky='nsew')
        self.log=tk_logger(self.root,self.mon); self._img=None; self._tk=None
        self.canvas.bind('<Configure>', lambda e:self._render())
    def listen_pair(self,box,robot_port=5001,vision_port=5002):
        box.set_logger(self.log)
        listen_in_thread(robot_port,'Lua',box.set('robot'),self.log)
        listen_in_thread(vision_port,'DVS',box.set('vision'),self.log)
    def buttons(self, items):
        for i,(txt,cmd) in enumerate(items): tk.Button(self.robot,text=txt,width=12,command=cmd).grid(row=i,column=0,padx=6,pady=4)
    def clear_image(self,text=None):
        def u(): self._img=None; self._tk=None; self.canvas.delete('all'); self.canvas.create_text(360,270,text=text or self.text['new_photo'],fill='#555')
        self.root.after(0,u)
    def show_image(self,path):
        def u():
            p=Path(path)
            if not p.exists() or Image is None:
                self.clear_image(self.text['missing_image']); return
            self._img=Image.open(p).convert('RGB'); self._render()
            self.root.after(120,self._render)
        self.root.after(0,u)
    def _render(self):
        if self._img is None or ImageTk is None: return
        cw=max(10,self.canvas.winfo_width()); ch=max(10,self.canvas.winfo_height())
        w,h=self._img.size; scale=min(cw/w,ch/h); size=(max(1,int(w*scale)),max(1,int(h*scale)))
        res=getattr(Image,'Resampling',Image).LANCZOS
        img=self._img.resize(size,res); self._tk=ImageTk.PhotoImage(img)
        self.canvas.delete('all'); self.canvas.create_image(cw//2,ch//2,image=self._tk,anchor='center')
    def run(self): self.root.mainloop()

def make_panel(box,robot_port=5001,vision_port=5002,text=None):
    p=ControlPanel(text=text); p.listen_pair(box,robot_port,vision_port); return p
