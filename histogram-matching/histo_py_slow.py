#! /bin/env python
"""
pure python implementation of histogram matching
"""

import math
import itertools
import time
from collections import defaultdict
from PIL import Image

#import imageio.v3 as iio
#image = iio.imread(uri="data/maize-root-cluster.jpg")

#import cv2
#cv2.imread('delme.jpg')

def make_cdf_pure_one(a):
    # h=array.array('L', [0]*256)
    h=[0]*256
    for v in a:
        h[v]+=1
    #cdf=array.array('f', [h[i] for i in range(256)])
    cdf=[h[i] for i in range(256)]
    for i in range(1, 256):
        cdf[i]+=cdf[i-1]
    for i in range(0, 256):
        cdf[i]/=cdf[255]
    return cdf

def make_cdf_pure(a):
    h0 = make_cdf_pure_one(a[0])
    h1 = make_cdf_pure_one(a[1])
    h2 = make_cdf_pure_one(a[2])
    return (h0, h1, h2)

def norm_a(a):
    size = len(a)
    return (
        bytearray(( a[i][0] for i in range(size) )),
        bytearray(( a[i][1] for i in range(size) )),
        bytearray(( a[i][2] for i in range(size) )),
    )

def get_histo_match_map_one(cdf_ref, cdf_in):
    mapping = bytearray(256)
    f=cdf_in[0]
    k=0 # k is in ref space
    # i is in src space
    for i, f in enumerate(cdf_in):
        while (cdf_ref[k]<f and k<255):
            k+=1
        mapping[i]=k
    return mapping

def a_T(a_out):
    a_out = bytearray(itertools.chain(*zip(*a_out)))
    return a_out

def a_T_alt(a_out):
    a_out2 = bytearray([0]*(len(a_out[0])*3))
    j=0
    for i in range(0, len(a_out2), 3):
        a_out2[i]=a_out[0][j]
        a_out2[i+1]=a_out[1][j]
        a_out2[i+2]=a_out[2][j]
        j+=1 
    return a_out2

def a_T_alt2(a_out):
    n = len(a_out[0])
    N = n*3
    a_out2 = bytearray((a_out[i%3][i//3] for i in range(N)))
    return a_out2


def histo_img(img_ref, img_in):
    a_ref = norm_a(img_ref.getdata())
    a_in = norm_a(img_in.getdata())
    t0=time.time()
    cdf_ref = make_cdf_pure(a_ref)
    dt=int((time.time()-t0)*1000.0)
    print(f"cdf_ref took {dt} ms")
    t0=time.time()
    cdf_in = make_cdf_pure(a_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"cdf_in took {dt} ms")
    t0=time.time()
    mapping = (
        get_histo_match_map_one(cdf_ref[0], cdf_in[0]),
        get_histo_match_map_one(cdf_ref[1], cdf_in[1]),
        get_histo_match_map_one(cdf_ref[2], cdf_in[2]),
    )
    dt=int((time.time()-t0)*1000.0)
    print(f"mapping took {dt} ms")
    t0=time.time()
    mapping0=mapping[0]
    mapping1=mapping[1]
    mapping2=mapping[2]
    a_out = (
        bytearray((mapping0[i] for i in a_in[0])),
        bytearray((mapping1[i] for i in a_in[1])),
        bytearray((mapping2[i] for i in a_in[2])),
    )
    dt=int((time.time()-t0)*1000.0)
    print(f"np.take took {dt} ms")
    t0=time.time()
    a_out = a_T(a_out)
    #a_out = a_T_alt(a_out)
    #a_out = a_T_alt2(a_out)
    dt=int((time.time()-t0)*1000.0)
    print(f"a.T took {dt} ms")
    return a_out

def histo(img_ref, img_in):
    t0=time.time()
    a_out = histo_img(img_ref, img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"histo_img took {dt} ms")
    t0=time.time()
    h, w = img_in.size
    # a_out = [list(zip(a_out[0][i:i+w], a_out[1][i:i+w], a_out[2][i:i+w])) for i in range(0, len(a_out), w)]
    img = Image.frombuffer('RGB', img_in.size, bytes(a_out))
    dt=int((time.time()-t0)*1000.0)
    print(f"array to img {dt} ms")
    return img

def main():
    fn_in="img/img05.jpg"
    fn_ref="img/img07.jpg"
    img_in=Image.open(fn_in).convert('RGB')
    img_ref=Image.open(fn_ref).convert('RGB')
    t0=time.time()
    img_out=histo(img_ref, img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"all took {dt} ms")
    t0=time.time()
    img_out=histo(img_ref, img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"all took {dt} ms")
    img_out.save('delme.jpg')

main()

