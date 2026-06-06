from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import random, shutil
IMG_SUFFIX={'.jpg','.jpeg','.png','.bmp','.tif','.tiff'}
@dataclass(frozen=True)
class DetectionResult:
    label: str; confidence: float; center_x: float; center_y: float; box: tuple[float,float,float,float]; image_path: Path|None=None

def find_images(folder):
    p=Path(folder); return sorted([x for x in p.iterdir() if x.is_file() and x.suffix.lower() in IMG_SUFFIX]) if p.exists() else []

def load_detector(model_path='models/best.pt'):
    p=Path(model_path)
    if not p.exists():
        cand=sorted(Path.cwd().glob('runs/**/weights/best.pt'), key=lambda x:x.stat().st_mtime, reverse=True)
        if cand:
            p.parent.mkdir(exist_ok=True); shutil.copy2(cand[0],p)
        else: raise FileNotFoundError(f'找不到模型文件: {p}，请先运行 module_b.py 训练')
    from ultralytics import YOLO
    return YOLO(str(p))

def _name(model,i):
    n=getattr(model,'names',{})
    return str(n.get(i,i) if isinstance(n,dict) else n[i])

def detect_objects(model, image, labels=None, conf=0.7, imgsz=1280, max_det=10, device=None):
    image=Path(image)
    res=model.predict(source=str(image), conf=conf, imgsz=imgsz, max_det=max_det, device=device, save=False, verbose=False)
    allow=set(labels or [])
    out=[]
    for r in res:
        for b in getattr(r,'boxes',[]) or []:
            lab=_name(model,int(b.cls[0]))
            if allow and lab not in allow: continue
            x1,y1,x2,y2=[float(x) for x in b.xyxy[0]]
            out.append(DetectionResult(lab,float(b.conf[0]),(x1+x2)/2,(y1+y2)/2,(x1,y1,x2,y2),image))
    return out

def keep_best_per_label(ds, order=None):
    best={}
    for d in ds:
        if d.label not in best or d.confidence>best[d.label].confidence: best[d.label]=d
    return [best[x] for x in order if x in best] if order else list(best.values())

def save_visualization(image_path, detections, output_path):
    image_path=Path(image_path); output_path=Path(output_path); output_path.parent.mkdir(parents=True,exist_ok=True)
    try:
        import cv2
        img=cv2.imread(str(image_path))
        if img is not None:
            h,w=img.shape[:2]; lw=max(2,int(min(w,h)/350)); fs=max(0.6,min(w,h)/1300)
            colors={'GPS':(255,80,20),'CHIP':(0,220,255),'WIFI':(255,255,255),'Square_red':(0,255,255),'Square_yellow':(255,0,0),'Square_silver':(255,0,255)}
            for d in detections:
                x1,y1,x2,y2=map(int,d.box); c=colors.get(d.label,(0,255,0)); cv2.rectangle(img,(x1,y1),(x2,y2),c,lw)
                txt=f'{d.label} {d.confidence:.2f}'; (tw,th),base=cv2.getTextSize(txt,cv2.FONT_HERSHEY_SIMPLEX,fs,lw)
                ty=max(th+8,y1-8); tx=max(0,min(x1,w-tw-8)); cv2.rectangle(img,(tx,ty-th-base-8),(tx+tw+8,ty+base),c,-1)
                cv2.putText(img,txt,(tx+4,ty-5),cv2.FONT_HERSHEY_SIMPLEX,fs,(20,20,20),lw,cv2.LINE_AA)
            cv2.imwrite(str(output_path),img); return output_path
    except Exception: pass
    from PIL import Image, ImageDraw, ImageFont
    im=Image.open(image_path).convert('RGB'); dr=ImageDraw.Draw(im); font=ImageFont.load_default()
    for d in detections:
        dr.rectangle(d.box,outline='red',width=3); dr.text((d.box[0],max(0,d.box[1]-14)),f'{d.label} {d.confidence:.2f}',fill='red',font=font)
    im.save(output_path); return output_path

def show_yolo_image(panel, image, dets, log=None, out_dir='images/predict_result', text=None):
    out=save_visualization(image,dets,Path(out_dir)/(Path(image).stem+'_result.jpg'))
    panel.show_image(out)
    if log:
        label=(text or {}).get('detect_image','detect image') if isinstance(text,dict) else 'detect image'
        log(label+':'+str(out))
    return out

def write_data_yaml(dataset,names):
    p=Path(dataset).resolve(); out=p/'data.yaml'; out.parent.mkdir(exist_ok=True)
    out.write_text('path: '+str(p).replace('\\','/')+'\ntrain: images/train\nval: images/val\nnames:\n'+'\n'.join(f'  {i}: {n}' for i,n in enumerate(names))+'\n',encoding='utf-8')
    return out

def auto_dataset(dataset,names):
    root=Path(dataset); im=root/'images'; la=root/'labels'; pairs=[]
    for img in find_images(im):
        lab=la/(img.stem+'.txt')
        if lab.exists(): pairs.append((img,lab))
    if pairs:
        for rel in ['images/train','images/val','labels/train','labels/val']:
            d=root/rel
            if d.exists(): shutil.rmtree(d)
            d.mkdir(parents=True,exist_ok=True)
        random.seed(0); random.shuffle(pairs)
        vc=max(1,min(len(pairs)-1,int(len(pairs)*0.2))) if len(pairs)>1 else 1
        tr=pairs[vc:] or pairs; va=pairs[:vc]
        for split,items in [('train',tr),('val',va)]:
            for img,lab in items:
                shutil.copy2(img,root/'images'/split/img.name); shutil.copy2(lab,root/'labels'/split/lab.name)
        print(f'[OK] 自动划分数据集 train:{len(tr)} val:{len(va)}')
    y=write_data_yaml(root,names)
    if not find_images(root/'images/train') or not find_images(root/'images/val'): raise FileNotFoundError(f'训练/验证图片为空，请把图片放到 {root}/images，标注放到 {root}/labels')
    return y

def default_device():
    try:
        import torch
        return 0 if torch.cuda.is_available() else 'cpu'
    except Exception: return 'cpu'

def train_params(cpu=False):
    return dict(epochs=60 if cpu else 120,imgsz=640 if cpu else 1280,batch=2 if cpu else 4,device='cpu' if cpu else 'auto',workers=0,cache=True,optimizer='AdamW',lr0=0.0008,patience=30,amp=False,mosaic=0,fliplr=0,flipud=0,degrees=8,translate=0.06,scale=0.15)

def train_yolo(model,data_yaml,project='runs/train',name='raicom_chip',**kw):
    if str(kw.get('device','auto')).lower()=='auto': kw['device']=default_device()
    from ultralytics import YOLO
    return YOLO(str(model)).train(data=str(Path(data_yaml).resolve()),project=str(Path(project).resolve()),name=name,exist_ok=True,**kw)

def copy_best(result=None,dst='models/best.pt'):
    src=Path(getattr(result,'save_dir','runs/train/raicom_chip'))/'weights/best.pt'
    if not src.exists(): src=sorted(Path.cwd().glob('runs/**/weights/best.pt'),key=lambda x:x.stat().st_mtime,reverse=True)[0]
    dst=Path(dst); dst.parent.mkdir(exist_ok=True); shutil.copy2(src,dst); return dst

def print_plan(yaml,classes,params):
    print('data.yaml:',yaml); print('classes:',', '.join(classes)); print('imgsz:',params['imgsz']); print('epochs:',params['epochs']); print('batch:',params['batch']); print('device:',params['device'])
