#!/usr/bin/env python3
"""Foto kalite puani. score.py KLASOR CIKTI.json  (tekrar calistirilabilir, 150 sn'de durur)"""
import sys,os,json,time
from PIL import Image,ImageOps,ImageFilter,ImageStat
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception: pass
d,out=sys.argv[1],sys.argv[2]; R=json.load(open(out)) if os.path.exists(out) else {}; t0=time.time()
fs=sorted(f for f in os.listdir(d) if f.lower().endswith(('.jpg','.jpeg','.heic','.png')))
for f in fs:
    if f in R: continue
    if time.time()-t0>150: break
    p=os.path.join(d,f)
    try:
        im=Image.open(p); ex=im.getexif(); dt=str(ex.get_ifd(0x8769).get(36867) or ex.get(306) or '')
        W,H=im.size
        try: im.draft('RGB',(800,800))
        except Exception: pass
        im=ImageOps.exif_transpose(im).convert('L'); im.thumbnail((600,600))
        sharp=ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).var[0]; bright=ImageStat.Stat(im).mean[0]
        sm=im.resize((9,8)); px=list(sm.getdata()); h=''.join('1' if px[r*9+c]>px[r*9+c+1] else '0' for r in range(8) for c in range(8))
        R[f]=dict(dt=dt,w=W,h=H,sharp=round(sharp,1),bright=round(bright,1),hash=h,kb=os.path.getsize(p)//1024)
    except Exception as e: R[f]=dict(err=str(e)[:80])
json.dump(R,open(out,'w'))
print(d,len(R),'/',len(fs))
