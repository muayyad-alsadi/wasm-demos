#! /bin/env python
"""
pure python implementation of histogram matching
"""

import math
import time
import numpy as np
import array
import itertools
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
    a_out = np.array((
        bytearray(mapping[0][i] for i in a_in[0]),
        bytearray(mapping[1][i] for i in a_in[1]),
        bytearray(mapping[2][i] for i in a_in[2]),
    ), np.uint8).T
    dt=int((time.time()-t0)*1000.0)
    print(f"np.take took {dt} ms")
    return a_out

def histo(img_ref, img_in):
    h,w=img_in.size
    t0=time.time()
    a_out = histo_img(img_ref, img_in)
    a_out = np.array(a_out, dtype=np.uint8).reshape((w,h,3))
    dt=int((time.time()-t0)*1000.0)
    print(f"histo_img took {dt} ms")
    t0=time.time()
    img=Image.fromarray(a_out, 'RGB')
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

