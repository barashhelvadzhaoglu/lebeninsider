#!/usr/bin/env python3
"""Taslak dikey short olusturur (sessiz). Kullanim: build.py KAYNAK_KOK CIKTI.mp4 oge1 oge2 ...
oge: 'IMG_7784.JPG' (2.3 sn foto) ya da 'IMG_7867.MOV@2' (2. saniyeden 3 sn klip)."""
import sys,os,subprocess,glob,tempfile
from PIL import Image,ImageOps
root,out,items=sys.argv[1],sys.argv[2],sys.argv[3:]
tmp=tempfile.mkdtemp(); segs=[]
def find(n): return glob.glob(os.path.join(root,'*',n))[0]
for i,it in enumerate(items):
    s=os.path.join(tmp,f'{i:03d}.mp4')
    if '.MOV' in it:
        n,_,st=it.partition('@'); st=st or '0'
        vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"
        cmd=['ffmpeg','-nostdin','-v','error','-y','-ss',st,'-t','3','-i',find(n),'-an','-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','21',s]
    else:
        im=ImageOps.exif_transpose(Image.open(find(it))).convert('RGB')
        r=max(1080/im.width,1920/im.height); im=im.resize((round(im.width*r)+1,round(im.height*r)+1))
        l=(im.width-1080)//2; t=(im.height-1920)//2; im=im.crop((l,t,l+1080,t+1920))
        p=os.path.join(tmp,f'{i:03d}.jpg'); im.save(p,quality=92)
        vf="zoompan=z='1+0.0015*on':d=69:s=1080x1920:fps=30,format=yuv420p"
        cmd=['ffmpeg','-nostdin','-v','error','-y','-i',p,'-vf',vf,'-frames:v','69','-c:v','libx264','-preset','veryfast','-crf','21',s]
    subprocess.run(cmd,check=True); segs.append(s)
lst=os.path.join(tmp,'l.txt'); open(lst,'w').write(''.join(f"file '{x}'\n" for x in segs))
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','concat','-safe','0','-i',lst,'-c','copy','-movflags','+faststart',out],check=True)
print(out, len(segs))
