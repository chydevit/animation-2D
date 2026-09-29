# Contact sheet of shot mid-frames for visual QA:  contact.py out.png id id id ...
import sys, numpy as np, skia
from multiprocessing import Pool
import render as R
def one(i):
    tl=R.TL(); sh=tl["shots"][i]; t=sh["t0"]+sh["dur"]*0.55
    arr=np.zeros((R.H,R.W,4),np.uint8); s=skia.Surface(arr); R.draw_frame(s.getCanvas(),t,sh)
    return i, arr[::3,::3].copy()
if __name__=="__main__":
    out=sys.argv[1]; ids=[int(a) for a in sys.argv[2:]]
    with Pool(3) as p: res=dict(p.map(one,ids))
    cols=3; rows=(len(ids)+cols-1)//cols
    h,w=R.H//3,R.W//3
    sheet=np.zeros((rows*(h+6),cols*(w+6),4),np.uint8); sheet[...,3]=255
    for k,i in enumerate(ids):
        r,c=divmod(k,cols); sheet[r*(h+6):r*(h+6)+h, c*(w+6):c*(w+6)+w]=res[i]
    img=skia.Image.fromarray(sheet); img.save(out, skia.kPNG); print("ok",out)
