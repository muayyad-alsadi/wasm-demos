"""
This class is used to workaround a bottleneck in wasmtime

* https://github.com/bytecodealliance/wasmtime-py/issues/81
* https://github.com/bytecodealliance/wasmtime-py/pull/134
"""

import ctypes
import array

from typing import Union

class FastMemory:
    def __init__(self, memory, store):
        self._memory = memory
        self._store = store

    def __getitem__(self, key: Union[int, slice]):
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
        # if not int, then it must be slice
        if not isinstance(key, slice):
            raise TypeError("key can either be integer index or slice")

        start, stop, step = key.indices(size)
        # this is tested with [1:4:2]
        if step!=1:
            raise ValueError("slice with step is not supported")

        val_size = stop - start
        value = bytearray(val_size)

        ptr_type = ctypes.c_ubyte * val_size
        dst_ptr = (ptr_type).from_buffer(value)
        src_ptr = ctypes.addressof((ptr_type).from_address(ctypes.addressof(data_ptr.contents)+start))
        ctypes.memmove(dst_ptr, src_ptr, val_size)
        return value

    def __setitem__(self, key: Union[int, slice], value: Union[bytearray, array.array]):
        """
        provide setter for memory[key] with slice support

        memory[offset]=value
        memory[start:stop]=b'hello world'
        memory[start:stop]=bytearray([1,2,3])
        """
        if self._store is None:
            raise RuntimeError("you must call `set_store()` before using highlevel access")

        data_ptr = self._memory.data_ptr(self._store)
        size = self._memory.data_len(self._store)
        if isinstance(key, int):
            if key>=size:
                raise IndexError("out of memory size")
            data_ptr[key] = value
            return value
        # if not int then it must be a slice
        if not isinstance(key, slice):
            raise TypeError("key can either be integer index or slice")

        # if it's a slice then value must be bytearray ex. cast bytes() to bytearray
        if not isinstance(value, array.array) and not isinstance(value, bytearray):
            # value = array.array('B', value)
            value = bytearray(value)

        start, stop, step = key.indices(size)
        if step!=1:
            raise ValueError("slice with step is not supported")

        val_size = len(value)
        # key.indices(size) knows about size but not val_size
        stop = start+min(stop-start, val_size)

        # NOTE: we can use * 1, because we need pointer to the start only
        ptr_type = ctypes.c_ubyte * val_size 
        src_ptr = (ptr_type).from_buffer(value)
        dst_ptr = ctypes.addressof((ptr_type).from_address(ctypes.addressof(data_ptr.contents)+start))
        ctypes.memmove(dst_ptr, src_ptr, val_size)
