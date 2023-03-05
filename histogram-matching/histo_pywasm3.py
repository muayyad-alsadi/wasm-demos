#! /bin/env python
"""
call WASM function from inside python using wasm3 interpreter
"""

# pip install --user wasm3

import math
import time
import numpy as np
import array
import itertools
from PIL import Image

import wasm3

size64k=64*1024

env = wasm3.Environment()
# stack size
rt  = env.new_runtime(40*1024)
with open('histo_match.wasm', 'rb') as f:
    mod = env.parse_module(f.read())

rt.load(mod)
memory=rt.get_memory(0)
hb=mod.get_global('__heap_base')
memory_grow=rt.find_function('memory_grow')
histo_match=rt.find_function('histo_match')



def img2array(img):
    # return list(itertools.chain(*img.getdata()))
    # return bytearray([ d1 for d2 in d3 for d1 in d2 ])
    a = np.array(img, dtype=np.uint8)
    if a.shape[-1]==3:
        a=np.pad(a, ((0,0),(0,0),(0,1)), constant_values=255)
    # a.flatten().tobytes()
    return bytearray(a.flatten())

def histo(img_ref, img_in):
    global memory
    h,w=img_in.size
    t0=time.time()
    a_ref=img2array(img_ref)
    a_in=img2array(img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"img2bytearray took {dt} ms")
    target_size = 20*size64k+hb+len(a_ref)+2*len(a_in)
    print(len(memory))
    growth = math.ceil((target_size-len(memory))/size64k)
    if growth>0:
        print("grow: ", growth)
        print(memory_grow(growth))
        memory=rt.get_memory(0)
    t0=time.time()
    memory[0:len(a_ref)]=a_ref
    memory[len(a_ref): len(a_ref)+len(a_in)]=a_in
    dt=int((time.time()-t0)*1000.0)
    print(f"slice set took {dt} ms")
    t0=time.time()
    histo_match(len(a_ref), hb, len(a_in), hb+len(a_ref), hb+len(a_ref)+len(a_in))
    dt=int((time.time()-t0)*1000.0)
    print(f"wasm took {dt} ms")
    t0=time.time()
    a_dst = np.array(memory[len(a_ref)+len(a_in):len(a_ref)+len(a_in)+len(a_in)], dtype=np.uint8).reshape((w,h,4))[:,:,:3]
    dt=int((time.time()-t0)*1000.0)
    print(f"slice to array {dt} ms")
    t0=time.time()
    img=Image.fromarray(a_dst, 'RGB')
    dt=int((time.time()-t0)*1000.0)
    print(f"array to image {dt} ms")
    return img

def main():
    fn_in="img/img05.jpg"
    fn_ref="img/img07.jpg"
    img_in=Image.open(fn_in).convert('RGBA')
    img_ref=Image.open(fn_ref).convert('RGBA')
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
