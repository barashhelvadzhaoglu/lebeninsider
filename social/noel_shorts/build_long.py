#!/usr/bin/env python3
"""Yatay uzun video (1920x1080). build_long.py SPEC.json ; tekrar calistirilabilir (segmentleri onbellekte tutar).
spec: out, root, title, sub, items[] ('IMG_x.jpeg' 4 sn foto | 'IMG_x.MOV@bas@sure' orijinal sesli klip), cache"""
import sys,os,subprocess,json,glob,time
from PIL import Image,ImageOps,ImageFilter,ImageDraw,ImageFont
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception: pass
S=json.load(open(sys.argv[1])); C=S['cache']; os.makedirs(C,exist_ok=True); t0=time.time()
F='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def find(n): return glob.glob(os.path.join(S['root'],'**',n),recursive=True)[0]
def frame(im,first=False):
    im=ImageOps.exif_transpose(im).convert('RGB')
    bg=im.resize((1920,round(im.height*1920/im.width))) if im.width/im.height<16/9 else im.resize((round(im.width*1080/im.height),1080))
    l=(bg.width-1920)//2;t=(bg.height-1080)//2; bg=bg.crop((l,t,l+1920,t+1080)).filter(ImageFilter.GaussianBlur(40))
    r=min(1920/im.width,1080/im.height); fg=im.resize((round(im.width*r),round(im.height*r)))
    bg.paste(fg,((1920-fg.width)//2,(1080-fg.height)//2))
    if first:
        d=ImageDraw.Draw(bg,'RGBA'); d.rectangle((0,760,1920,1000),fill=(0,0,0,150))
        for txt,sz,y in [(S['title'],80,790),(S['sub'],44,900)]:
            f=ImageFont.truetype(F,sz); w=d.textlength(txt,font=f); d.text(((1920-w)/2,y),txt,font=f,fill='white')
    return bg
segs=[]
for i,it in enumerate(S['items']):
    s=os.path.join(C,f'{i:03d}.ts'); segs.append(s)
    if os.path.exists(s): continue
    if time.time()-t0>150: print('ZAMAN: tekrar calistir'); sys.exit(2)
    if '.MOV' in it:
        n,st,du=it.split('@')
        vf="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p"
        cmd=['ffmpeg','-nostdin','-v','error','-y','-ss',st,'-t',du,'-i',find(n),'-f','lavfi','-t',du,'-i','anullsrc=r=48000:cl=stereo','-filter_complex',f'[0:v]{vf}[v];[0:a]aresample=48000,volume=0.8[a0];[a0][1:a]amix=inputs=2:duration=longest[a]','-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','22','-c:a','aac','-ar','48000','-ac','2','-t',du,s]
    else:
        p=s+'.jpg'; frame(Image.open(find(it)),i==0).save(p,quality=92)
        cmd=['ffmpeg','-nostdin','-v','error','-y','-loop','1','-i',p,'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-vf',"zoompan=z='1+0.0008*on':d=120:s=1920x1080:fps=30,format=yuv420p",'-frames:v','120','-t','4','-c:v','libx264','-preset','veryfast','-crf','22','-c:a','aac','-ar','48000','-ac','2','-shortest',s]
    r=subprocess.run(cmd)
    if r.returncode: print('HATA',it); os.path.exists(s) and os.remove(s); sys.exit(1)
lst=os.path.join(C,'l.txt'); open(lst,'w').write(''.join(f"file '{x}'\n" for x in segs))
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','concat','-safe','0','-i',lst,'-c','copy','-movflags','+faststart',S['out']],check=True)
print('BITTI',S['out'])
