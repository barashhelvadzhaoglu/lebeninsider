#!/usr/bin/env python3
"""Seslendirmeli dikey short. build2.py SPEC.json  -> spec: out, audio, roots[], items[], top, bottom[], note
oge: 'IMG_7784.JPG' foto, 'IMG_7867.MOV@2' klip (2. saniyeden)."""
import sys,os,subprocess,glob,tempfile,json
from PIL import Image,ImageOps,ImageDraw,ImageFont
try:
    import pillow_heif; pillow_heif.register_heif_opener()
except Exception: pass
S=json.load(open(sys.argv[1])); tmp=tempfile.mkdtemp(); segs=[]
dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',S['audio']]))+0.8
per=dur/len(S['items']); nf=round(per*30)
def find(n):
    for r in S['roots']:
        g=glob.glob(os.path.join(r,'**',n),recursive=True)
        if g: return g[0]
    raise SystemExit('yok: '+n)
for i,it in enumerate(S['items']):
    s=os.path.join(tmp,f'{i:03d}.mp4')
    if '.MOV' in it:
        n,_,st=it.partition('@')
        cmd=['ffmpeg','-nostdin','-v','error','-y','-ss',st or '0','-i',find(n),'-an','-vf',"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p",'-frames:v',str(nf),'-c:v','libx264','-preset','veryfast','-crf','21',s]
    else:
        im=ImageOps.exif_transpose(Image.open(find(it))).convert('RGB')
        r=max(1080/im.width,1920/im.height); im=im.resize((round(im.width*r)+1,round(im.height*r)+1))
        l=(im.width-1080)//2; t=(im.height-1920)//2; im=im.crop((l,t,l+1080,t+1920))
        p=os.path.join(tmp,f'{i:03d}.jpg'); im.save(p,quality=92)
        cmd=['ffmpeg','-nostdin','-v','error','-y','-i',p,'-vf',f"zoompan=z='1+0.0012*on':d={nf}:s=1080x1920:fps=30,format=yuv420p",'-frames:v',str(nf),'-c:v','libx264','-preset','veryfast','-crf','21',s]
    subprocess.run(cmd,check=True); segs.append(s)
# yazi katmani
F='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
ov=Image.new('RGBA',(1080,1920),(0,0,0,0)); d=ImageDraw.Draw(ov)
def block(lines,y,size,anchor_top=True):
    f=ImageFont.truetype(F,size); hs=[d.textbbox((0,0),l,font=f) for l in lines]
    h=sum(b[3]-b[1]+18 for b in hs)+30
    y0=y if anchor_top else y-h
    d.rounded_rectangle((60,y0,1020,y0+h),24,fill=(0,0,0,150)); yy=y0+20
    for l,b in zip(lines,hs):
        w=b[2]-b[0]; d.text(((1080-w)//2,yy),l,font=f,fill='white'); yy+=b[3]-b[1]+18
if S.get('top'): block(S['top'],170,62)
if S.get('bottom'): block(S['bottom'],1640,44,False)
if S.get('note'):
    f=ImageFont.truetype(F,28); w=d.textlength(S['note'],font=f); d.text(((1080-w)//2,1860),S['note'],font=f,fill=(255,255,255,190))
op=os.path.join(tmp,'ov.png'); ov.save(op)
lst=os.path.join(tmp,'l.txt'); open(lst,'w').write(''.join(f"file '{x}'\n" for x in segs))
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','concat','-safe','0','-i',lst,'-i',op,'-i',S['audio'],
  '-filter_complex','[0:v][1:v]overlay=0:0,format=yuv420p[v]','-map','[v]','-map','2:a','-c:v','libx264','-preset','veryfast','-crf','21','-c:a','aac','-b:a','160k','-movflags','+faststart',S['out']],check=True)
print(S['out'],round(dur,1))
