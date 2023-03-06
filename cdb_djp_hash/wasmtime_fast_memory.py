"""
This class is used to workaround a bottleneck in wasmtime

* https://github.com/bytecodealliance/wasmtime-py/issues/81
* https://github.com/bytecodealliance/wasmtime-py/pull/134
"""

import ctypes
import array

class FastMemory:
    def __init__(self, memory, store):
        self._memory=memory
        self._store=store

    def __getitem__(self, key: int):
        """
        provide memory[offset] or memory[start:stop]
        """
        if self._store is None:
            raise RuntimeError("you must call `set_store()` before using highlevel access")
        data_ptr = self._memory.data_ptr(self._store)
        size = self._memory.data_len(self._store)
        if isinstance(key, int):
            if key>=size:
                raise IndexError("out of memory size")
            return data_ptr[key]
        if not isinstance(key, slice):
            raise TypeError("key can either be integer index or slice")
        
        start, stop, step = key.indices(size)
        if step!=1:
            raise ValueError("slice with step is not supported")

        val_size = stop - start
        value = bytearray(val_size)

        if stop>size:
            raise IndexError("out of memory size")
        dst_ptr = (ctypes.c_ubyte * val_size).from_buffer(value)
        src_ptr = ctypes.addressof((ctypes.c_ubyte*val_size).from_address(ctypes.addressof(data_ptr.contents)+start))
        ctypes.memmove(dst_ptr, src_ptr, val_size)
        return value

    def __setitem__(self, key, value: bytearray):
        """
        provide setter for memory[key] with slice support

        memory[offset]=value
        memory[start:stop]=b'hello world'
        memory[start:stop]=bytearray([1,2,3])
        """
        if not isinstance(value, array.array) and not isinstance(value, bytearray):
            # value = array.array('B', value)
            value = bytearray(value)

        if self._store is None:
            raise RuntimeError("you must call `set_store()` before using highlevel access")
        data_ptr = self._memory.data_ptr(self._store)
        size = self._memory.data_len(self._store)
        if isinstance(key, int):
            if key>=size:
                raise IndexError("out of memory size")
            data_ptr[key] = value
        if not isinstance(key, slice):
            raise TypeError("key can either be integer index or slice")

        start, stop, step = key.indices(size)
        if step!=1:
            raise ValueError("slice with step is not supported")

        val_size = len(value)
        if stop is None:
            stop=start+val_size
        if stop-start>val_size or stop>size:
            raise IndexError("out of memory size")
        
        src_ptr = (ctypes.c_ubyte * val_size).from_buffer(value)
        dst_ptr = ctypes.addressof((ctypes.c_ubyte*val_size).from_address(ctypes.addressof(data_ptr.contents)+start))
        ctypes.memmove(dst_ptr, src_ptr, val_size)
