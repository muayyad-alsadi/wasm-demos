#! /bin/env python
"""
call WASM function from inside python using Wasmer

https://github.com/wasmerio/wasmer-python/issues/700
"""

# pip install --user wasmer wasmer-compiler-singlepass

import math
import time
import numpy as np
import array
import itertools
from PIL import Image

from wasmer import Store, Module, Instance


#import imageio.v3 as iio
#image = iio.imread(uri="delme.jpg")

#import cv2
#cv2.imread('delme.jpg')

store = Store()
module = Module(store, open('histo_match.wasm', 'rb').read())
instance = Instance(module)

size64k=64*1024

def img2array(img):
    # return list(itertools.chain(*img.getdata()))
    # return bytearray([ d1 for d2 in d3 for d1 in d2 ])
    a = np.array(img, dtype=np.uint8)
    if a.shape[-1]==3:
        a=np.pad(a, ((0,0),(0,0),(0,1)), constant_values=255)
    # a.flatten().tobytes()
    return bytearray(a.flatten())

def histo(img_ref, img_in):
    h,w=img_in.size
    t0=time.time()
    a_ref=img2array(img_ref)
    a_in=img2array(img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"img2bytearray took {dt} ms")
    hb = instance.exports.__heap_base.value
    target_size = 20*size64k+hb+len(a_ref)+2*len(a_in)
    growth = math.ceil((target_size-instance.exports.memory.data_size)/size64k)
    if growth>0:
        print("grow: ", growth)
        instance.exports.memory.grow(growth)
    t0=time.time()
    u8buf = instance.exports.memory.uint8_view(offset=hb)
    u8buf[0:len(a_ref)]=a_ref
    u8buf[len(a_ref): len(a_ref)+len(a_in)]=a_in
    dt=int((time.time()-t0)*1000.0)
    print(f"slice set took {dt} ms")
    t0=time.time()
    instance.exports.histo_match(len(a_ref), hb, len(a_in), hb+len(a_ref), hb+len(a_ref)+len(a_in))
    dt=int((time.time()-t0)*1000.0)
    print(f"wasm took {dt} ms")
    t0=time.time()
    a_dst = np.array(u8buf[len(a_ref)+len(a_in):len(a_ref)+len(a_in)+len(a_in)], dtype=np.uint8).reshape((w,h,4))[:,:,:3]
    dt=int((time.time()-t0)*1000.0)
    print(f"slice to array {dt} ms")
    t0=time.time()
    img=Image.fromarray(a_dst, 'RGB')
    dt=int((time.time()-t0)*1000.0)
    print(f"array to image {dt} ms")
    return img

def histo_buffer_protocol(img_ref, img_in):
    h,w=img_in.size
    t0=time.time()
    a_ref=img2array(img_ref)
    a_in=img2array(img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"img2bytearray took {dt} ms")
    hb = instance.exports.__heap_base.value
    target_size = 20*size64k+hb+len(a_ref)+2*len(a_in)
    growth = math.ceil((target_size-instance.exports.memory.data_size)/size64k)
    if growth>0:
        print("grow: ", growth)
        instance.exports.memory.grow(growth)
    t0=time.time()

    np_memory = np.frombuffer(instance.exports.memory.buffer, dtype=np.uint8,
            offset=hb)
    np_memory[0:len(a_ref)] = a_ref
    np_memory[len(a_ref): len(a_ref)+len(a_in)]=a_in
    dt=int((time.time()-t0)*1000.0)
    print(f"slice set took {dt} ms")
    t0=time.time()
    instance.exports.histo_match(len(a_ref), hb, len(a_in), hb+len(a_ref), hb+len(a_ref)+len(a_in))
    dt=int((time.time()-t0)*1000.0)
    print(f"wasm took {dt} ms")
    t0=time.time()
    a_dst = np_memory[len(a_ref)+len(a_in):len(a_ref)+len(a_in)+len(a_in)].reshape((w,h,4))[:,:,:3]
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

    print('Slicing')
    print('_______')
    t0=time.time()
    img_out=histo(img_ref, img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"all took {dt} ms\n")
    t0=time.time()
    img_out=histo(img_ref, img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"all took {dt} ms\n\n")
    img_out.save('wasmer_slice.jpg')

    print('Buffer Protocol')
    print('_______')
    t0=time.time()
    img_out=histo_buffer_protocol(img_ref, img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"all took {dt} ms\n")
    t0=time.time()
    img_out=histo_buffer_protocol(img_ref, img_in)
    dt=int((time.time()-t0)*1000.0)
    print(f"all took {dt} ms")

    img_out.save('wasmer_buffer_protocol.jpg')
main()
