import json,glob,collections,os
def ham(a,b): return sum(x!=y for x,y in zip(a,b))
out={}
for p in sorted(glob.glob('*.json')):
    if p.startswith('_'): continue
    d=p[:-5]; R=json.load(open(p)); ok=[(f,r) for f,r in R.items() if 'err' not in r]
    err=len(R)-len(ok); months=collections.Counter(r['dt'][:7] for f,r in ok)
    good=[];why=collections.Counter()
    for f,r in sorted(ok):
        mp=r['w']*r['h']/1e6
        if mp<2: why['dusuk_cozunurluk']+=1; continue
        if r['sharp']<60: why['bulanik']+=1; continue
        if r['bright']<25: why['cok_karanlik']+=1; continue
        good.append((f,r))
    uniq=[]
    for f,r in sorted(good,key=lambda x:-x[1]['sharp']):
        if any(ham(r['hash'],u[1]['hash'])<=6 and abs(int(f[4:8] if f[4:8].isdigit() else 0)-int(u[0][4:8] if u[0][4:8].isdigit() else 0))<15 for u in uniq): why['tekrar']+=1; continue
        uniq.append((f,r))
    seas=[f for f,r in uniq if r['dt'][5:7] in ('11','12') or r['dt'][5:7]=='01']
    out[d]=dict(toplam=len(R),hata=err,ay=dict(months.most_common(4)),elenen=dict(why),iyi=len(uniq),sezon=len(seas),liste=sorted(f for f,_ in uniq))
    print(f"{d:20s} toplam {len(R):4d} hata {err} iyi {len(uniq):3d} sezon(Kas-Oca) {len(seas):3d} | elenen {dict(why)} | aylar {dict(months.most_common(4))}")
json.dump(out,open('_ozet.json','w'),ensure_ascii=False)
