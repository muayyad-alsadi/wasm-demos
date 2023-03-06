#! /bin/env python
"""
call WASM function from inside python using wasmtime
"""

# pip install --user wasmtime


import timeit
import array
import functools

# you can import wasm files directly if loaded
# import wasmtime.loader
# import cdb_djp_hash

try:
    from cdblib import djb_hash as cdb_djp_hash_c
except: cdb_djp_hash_c=None

from cProfile import Profile

from wasmtime import Store, Module, Instance

from wasmtime_fast_memory import FastMemory

store = Store()
module = Module.from_file(store.engine, 'cdb_djp_hash.wasm')
instance = Instance(store, module, [])
memory = instance.exports(store)['memory']
fast_mem = FastMemory(memory, store)

__heap_base = instance.exports(store)['__heap_base']
hb=__heap_base.value(store)
_cdb_djp_hash_wasm = functools.partial(instance.exports(store)['cdb_djp_hash'], store)
size64k=64*1024

def cdb_djp_hash_wasm(input: bytearray):
    size = len(input)
    start = hb
    stop = start + size
    fast_mem[start:stop]=input
    return _cdb_djp_hash_wasm(start, size)

def cdb_djp_hash_pure(s):
    '''Return the value of DJB's hash function for byte string *s*'''
    h = 5381
    for c in s:
        h = (((h << 5) + h) ^ c) & 0xffffffff
    return h

input_b = b"Hello, world!"
input_a = bytearray(input_b)
#input_a = array.array('B', input_b)
large_b = b"Hello, world! "*100
large_a = bytearray(large_b)
large_a2 = array.array('B', large_b)

def main():
    hash_wasm  = cdb_djp_hash_wasm(input_a)
    hash_pure = cdb_djp_hash_pure(input_a)
    hash_c = cdb_djp_hash_c(input_b)
    print("validating same value", hex(hash_wasm), hex(hash_pure), hex(hash_c))
    print("*** hashing small data of size", len(input_b))
    #print(timeit.timeit(lambda: cdb_djp_hash_wasm(input_a), globals=globals(), number=1000))
    print("cdb_djp_hash_wasm(input_a)", timeit.timeit('cdb_djp_hash_wasm(input_a)', 'from __main__ import cdb_djp_hash_wasm, input_a', number=1000))
    print('cdb_djp_hash_pure(input_a)', timeit.timeit('cdb_djp_hash_pure(input_a)', 'from __main__ import cdb_djp_hash_pure, input_a', number=1000))
    if cdb_djp_hash_c:
        print("cdb_djp_hash_c(input_b)", timeit.timeit('cdb_djp_hash_c(input_b)', 'from __main__ import cdb_djp_hash_c, input_b', number=1000))
    else:
        print("cdb_djp_hash_c is not available install: `pip install --user pure-cdb`")
    print("*** hashing large data of size", len(large_b))
    #print(timeit.timeit(lambda: cdb_djp_hash_wasm(large_a), globals=globals(), number=1000))
    print("cdb_djp_hash_wasm(large_a)", timeit.timeit('cdb_djp_hash_wasm(large_a)', 'from __main__ import cdb_djp_hash_wasm, large_a', number=1000))
    print("cdb_djp_hash_wasm(large_a2)", timeit.timeit('cdb_djp_hash_wasm(large_a2)', 'from __main__ import cdb_djp_hash_wasm, large_a2', number=1000))
    print('cdb_djp_hash_pure(large_a)', timeit.timeit('cdb_djp_hash_pure(large_a)', 'from __main__ import cdb_djp_hash_pure, large_a', number=1000))
    if cdb_djp_hash_c:
        print("cdb_djp_hash_c(large_b)", timeit.timeit('cdb_djp_hash_c(large_b)', 'from __main__ import cdb_djp_hash_c, large_b', number=1000))
    else:
        print("cdb_djp_hash_c is not available install: `pip install --user pure-cdb`")
    #pr=Profile()
    #pr.enable()
    #for i in range(10000):
    #    cdb_djp_hash_wasm(large_a)
    #pr.disable()
    #pr.print_stats()
    #pr.print_stats('cumulative')
    #pr.print_stats('calls')

main()
