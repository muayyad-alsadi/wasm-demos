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
    for i in range(1, 256):
        cdf[i]/=cdf[255]
    return cdf

def make_cdf_pure_one_alt(a):
    h=np.array([0]*256, dtype=uint32)
    for v in a:
        h[v]+=1
    cdf=np.array([h[i] for i in range(256)], dtype=np.float32)
    for i in range(1, 256):
        cdf[i]+=cdf[i-1]
    cdf/=cdf[255]
    return cdf

def make_cdf_pure(a):
    h0 = make_cdf_pure_one(a[:, 0])
    h1 = make_cdf_pure_one(a[:, 1])
    h2 = make_cdf_pure_one(a[:, 2])
    return (h0, h1, h2)

def make_cdf_a(a):
    h0 = np.cumsum(np.histogram(a[:,0], bins=range(256))[0])
    h0 = h0/float(h0[-1])
    h1 = np.cumsum(np.histogram(a[:,1], bins=range(256))[0])
    h1 = h1/float(h1[-1])
    h2 = np.cumsum(np.histogram(a[:,2], bins=range(256))[0])
    h2 = h2/float(h2[-1])
    #h0 = np.cumsum(np.histogram(a[:,0], bins=range(257), range=(0, 255), density=True)[0])
    #h1 = np.cumsum(np.histogram(a[:,1], bins=range(257), range=(0, 255), density=True)[0])
    #h2 = np.cumsum(np.histogram(a[:,2], bins=range(257), range=(0, 255), density=True)[0])
    return (h0, h1, h2)

def make_cdf_img(img):
    a = np.cumsum(np.array(img.histogram()).reshape(3,256), axis=1)
    b = a[:, -1]
    return np.array((
        a[0]/float(b[0]),
        a[1]/float(b[1]),
        a[2]/float(b[2]),
        ), dtype=np.float32)

def norm_a(a):
    if a.shape[-1]==4:
        a = a[:,:,3]
    return a.reshape((-1,3))

def get_histo_match_map_one(cdf_ref, cdf_in):
    mapping = np.zeros((256), dtype=np.uint8)
    f=cdf_in[0]
    k=0 # k is in ref space
    # i is in src space
    for i, f in enumerate(cdf_in):
        while (cdf_ref[k]<f and k<255):
            k+=1
        mapping[i]=k
    return mapping

def histo_img(img_ref, img_in):
    a_ref = norm_a(np.array(img_ref, dtype=np.uint8))
    a_in = norm_a(np.array(img_in, dtype=np.uint8))
    t0=time.time()
    #cdf_ref = make_cdf_pure(a_ref)
    #cdf_ref = make_cdf_a(a_ref)
    cdf_ref = make_cdf_img(img_ref)
    dt=int((time.time()-t0)*1000.0)
    print(f"cdf_ref took {dt} ms")
    t0=time.time()
    #cdf_in = make_cdf_pure(a_in)
    #cdf_in = make_cdf_a(a_in)
    cdf_in = make_cdf_img(img_in)
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
        np.take(mapping[0], a_in[:, 0]),
        np.take(mapping[1], a_in[:, 1]),
        np.take(mapping[2], a_in[:, 2]),
    ), np.uint8).T
    dt=int((time.time()-t0)*1000.0)
    print(f"np.take took {dt} ms")
    return a_out

def histo(img_ref, img_in):
    h,w=img_in.size
    t0=time.time()
    a_out = histo_img(img_ref, img_in)
    a_out = a_out.reshape((w,h,3))
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

