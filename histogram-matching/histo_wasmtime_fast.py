#! /bin/env python
"""
call WASM function from inside python using wasmtime

see
* https://github.com/bytecodealliance/wasmtime-py/issues/81
* https://github.com/bytecodealliance/wasmtime-py/pull/134
"""

# pip install --user wasmtime

import math
import time
import numpy as np
from PIL import Image

import ctypes

# you can import wasm files directly if loaded
# import wasmtime.loader
# import histo_match

from wasmtime import Store, Module, Instance

store = Store()
module = Module.from_file(store.engine, 'histo_match.wasm')
instance = Instance(store, module, [])
memory = instance.exports(store)['memory']
memory_ptr = memory.data_ptr(store)
__heap_base = instance.exports(store)['__heap_base']
hb=__heap_base.value(store)
histo_match = instance.exports(store)['histo_match']
size64k=64*1024

def set_slice(val, start=0, end=None):
    size = memory.data_len(store)
    if end is None: end=start+len(val)
    val_size = len(val)
    if end-start>val_size or end>size:
        raise IndexError("out of memory size")
    src_ptr = (ctypes.c_ubyte * val_size).from_buffer(val)
    dst_ptr = ctypes.addressof((ctypes.c_ubyte*val_size).from_address(ctypes.addressof(memory_ptr.contents)+start))
    ctypes.memmove(dst_ptr, src_ptr, val_size)
    return


def get_slice(start=0, end=None):
    size = memory.data_len(store)
    if end is None: end=size
    if end>size:
        raise IndexError("out of memory size")
    val_size=end-start
    val=bytearray(val_size)
    dst_ptr = (ctypes.c_ubyte * val_size).from_buffer(val)
    src_ptr = ctypes.addressof((ctypes.c_ubyte*val_size).from_address(ctypes.addressof(memory_ptr.contents)+start))
    ctypes.memmove(dst_ptr, src_ptr, val_size)
    return val


# libname = '_libwasmtime.so'
# dll = cdll.LoadLibrary(filename)

# return ffi.wasmtime_memory_data(store._context, byref(self._memory))


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
    target_size = 20*size64k+hb+len(a_ref)+2*len(a_in)
    growth = math.ceil((target_size-memory.data_len(store))/size64k)
    if growth>0:
        print("grow: ", growth)
        print(memory.grow(store, growth))
        print(memory.data_len(store))
    t0=time.time()
    set_slice(a_ref)
    set_slice(a_in, len(a_ref))
    dt=int((time.time()-t0)*1000.0)
    print(f"slice set took {dt} ms")
    t0=time.time()
    histo_match(store, len(a_ref), hb, len(a_in), hb+len(a_ref), hb+len(a_ref)+len(a_in))
    dt=int((time.time()-t0)*1000.0)
    print(f"wasm took {dt} ms")
    t0=time.time()
    # dst=bytearray(memory.data_ptr(store)[len(a_ref)+len(a_in):len(a_ref)+len(a_in)+len(a_in)])
    dst = get_slice(len(a_ref)+len(a_in), len(a_ref)+len(a_in)+len(a_in))
    a_dst = np.array(dst, dtype=np.uint8).reshape((w,h,4))[:,:,:3]
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
