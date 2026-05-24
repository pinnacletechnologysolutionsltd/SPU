# -*- coding:utf-8 -*-

'''
Created on 2021.12
@author: tanjiaxi
'''

import os
import sys
import ctypes
import _ctypes
import struct

from . import structs
from . import errors


def output_func(msg):
    print(msg.decode())
    

class CKLink(object):
    """Python interface for the T-HEAD CKLink.
    """
    
    DLL_PATH = os.path.dirname(__file__)
    WORK_PATH = os.getcwd()

    def open_required(func):
        def wrapper(self, *args, **kwargs):
            if not self.tgt:
                raise errors.CKLinkException('Error: Target is not open')
            return func(self, *args, **kwargs)
        return wrapper
    
    def change_working_path(func):
        def wrapper(self, *args, **kwargs):
            os.chdir(CKLink.DLL_PATH)
            func(self, *args, **kwargs)
            os.chdir(CKLink.WORK_PATH)
        return wrapper

    def __init__(self, **kwargs):
        self.tgt = None
        self.cfg = structs.DebuggerDerverCfg()
        if "dlldir" in kwargs:
            CKLink.DLL_PATH = kwargs["dlldir"]
        else:
            CKLink.DLL_PATH = os.path.dirname(__file__)
        self.initialize(**kwargs)
    
    @change_working_path
    def initialize(self, **kwargs):
        self.find_library()
        self.dll_utils.init_default_config(ctypes.byref(self.cfg))
        self.cfg.root_path = CKLink.DLL_PATH.encode('utf-8')
        if "vid" in kwargs:
            self.cfg.link.vid = kwargs["vid"]
        if "pid" in kwargs:
            self.cfg.link.pid = kwargs["pid"]
        if "sn" in kwargs:
            self.cfg.link.serial = kwargs["sn"].encode('utf-8')           
        if "arch" in kwargs:
            self.cfg.arch.debug_arch = kwargs["arch"]  # 0:none, 1:csky, 2:riscv, 3:auto
        if "cdi" in kwargs:
            self.cfg.link.cdi = kwargs["cdi"]  # JTAG=0/SWD=1
        self.cfg.arch.no_cache_flush = 1  # 执行单步和退出调试模式时不刷cache, 提高烧写速度
        self.dll_utils.dbg_debug_channel_init(self.cfg.misc.msgout, self.cfg.misc.errout, self.cfg.misc.verbose)
        self.dll_target.target_init.argtypes = [ctypes.POINTER(structs.DebuggerDerverCfg)]
        self.dll_target.target_init(ctypes.byref(self.cfg))
           
    def find_library(self):
        if sys.platform == 'win32':
            python_version = struct.calcsize("P") * 8
            if python_version == 32:
                self.dll_target = ctypes.cdll.LoadLibrary(os.path.join(CKLink.DLL_PATH, "Target.dll"))
                self.dll_utils = ctypes.cdll.LoadLibrary(os.path.join(CKLink.DLL_PATH, "Utils.dll"))
            else:
                raise errors.CKLinkException('Error: Python must be 32-bit version')
        elif sys.platform.startswith('linux'):
            self.dll_stdc = ctypes.CDLL(os.path.join(CKLink.DLL_PATH, "libstdc++.so.6"), mode=ctypes.RTLD_GLOBAL)        
            self.dll_usb = ctypes.CDLL(os.path.join(CKLink.DLL_PATH, "libusb-1.0.so"), mode=ctypes.RTLD_GLOBAL)
            self.dll_utils = ctypes.CDLL(os.path.join(CKLink.DLL_PATH, "libUtils.so"), mode=ctypes.RTLD_GLOBAL)
            self.dll_cklink = ctypes.CDLL(os.path.join(CKLink.DLL_PATH, "links/CK-Link/libCklink.so"), mode=ctypes.RTLD_GLOBAL)
            self.dll_scripts = ctypes.CDLL(os.path.join(CKLink.DLL_PATH, "libScripts.so"), mode=ctypes.RTLD_GLOBAL)
            self.dll_xml = ctypes.CDLL(os.path.join(CKLink.DLL_PATH, "libXml.so"), mode=ctypes.RTLD_GLOBAL)
            self.dll_target = ctypes.CDLL(os.path.join(CKLink.DLL_PATH, "libTarget.so"))
                                
    def print_version(self):
        fn_type_output = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
        self.output = fn_type_output(output_func)
        self.dll_target.target_print_version(self.output)
    
    def connected(self):
        """Returns whether a CKLink is connected.

        Args:
          self (CKLink): the ``CKLink`` instance

        Returns:
          ``True`` if the CKLink is open and connected, otherwise ``False``.
        """
        if self.tgt:
            res = self.dll_target.target_is_connected(self.tgt)
            return True if res else False
        else: 
            return False

    def open(self):
        self.dll_target.target_open.argtypes = [ctypes.POINTER(structs.DebuggerDerverCfg)]
        self.dll_target.target_open.restype = ctypes.POINTER(structs.Target)
        self.tgt = self.dll_target.target_open(ctypes.byref(self.cfg))
        self.cfg.target = self.tgt.contents
        # print("handle is " + str(self.tgt))
        # return a handle(an address comes from malloc)
        if not self.tgt:
            raise errors.CKLinkException('Error: Open target failed')
    
    def close(self):
        if self.tgt:
            self.dll_target.target_close.argtypes = [ctypes.POINTER(structs.Target)]
            res = self.dll_target.target_close(self.tgt)
            if not res:
                self.tgt = None
                return True
            else:
                return False 
  
    @open_required
    def halt(self):
        """Halt the target
        
        Args:
          self (CKLink): the ``CKLink`` instance

        Returns:
          ``True`` if halted, ``False`` otherwise.
        """
        self.dll_target.target_halt.argtypes = [ctypes.POINTER(structs.Target)]
        res = self.dll_target.target_halt(self.tgt)
        return True if not res else False
    
    @open_required
    def reset(self, type=1):
        """Reset the target
        
        Args:
          self (CKLink): the ``CKLink`` instance
          type (int): 2, nreset, 1 hard, 0, software

        Returns:
          ``True`` if success, ``False`` otherwise.
        """
        self.dll_target.target_reset.argtypes = [ctypes.POINTER(structs.Target), ctypes.c_uint]
        res = self.dll_target.target_reset(self.tgt, type)
        return True if not res else False
    
    @open_required
    def resume(self):
        self.dll_target.target_resume.argtypes = [ctypes.POINTER(structs.Target)]
        res = self.dll_target.target_resume(self.tgt)
        return True if not res else False
      
    @open_required
    def write_memory(self, addr, data):
        """Write memory to target

        Args:
          self (CKLink): the ``CKLink`` instance
          addr (int): start address to write to
          data (bytes): data to write

        Returns:
          ``True`` if success, ``False`` otherwise
        """
        addr = ctypes.c_uint64(addr)
        size = len(data)
        wbuff = (ctypes.c_char*size)(*(data))
        self.dll_target.target_write_memory.argtypes = [ctypes.POINTER(structs.Target), ctypes.c_uint64, ctypes.c_char_p]
        res = self.dll_target.target_write_memory(self.tgt, addr, wbuff, size)
        return True if not res else False 
    
    @open_required
    def read_memory(self, addr, size):
        """Read memory from target

        Args:
          self (CKLink): the ``CKLink`` instance
          addr (int): start address to read from
          size (int): size to read

        Returns:
          data (bytes) read from memory
        """
        addr = ctypes.c_uint64(addr)
        rbuff = (ctypes.c_char*size)()
        self.dll_target.target_read_memory.argtypes = [ctypes.POINTER(structs.Target), ctypes.c_uint64, ctypes.c_char_p, ctypes.c_uint]
        res = self.dll_target.target_read_memory(self.tgt, addr, rbuff, size)
        if not res:
            return rbuff[:]
        else:
            raise errors.CKLinkException('Error: Read memory failed')
    
    @open_required
    def write_cpu_reg(self, reg_index, value):
        """Write cpu register
        
        Args:
          self (CKLink): the ``CKLink`` instance
          reg_index (int): reigster to be written
          value (int): the value to write to the register
          
        Returns:
          ``True`` if success, ``False`` otherwise
        """
        rn = structs.Register()
        rn.num = reg_index
        rn.value.val32 = value
        self.dll_target.target_write_cpu_reg.argtypes = [ctypes.POINTER(structs.Target), ctypes.POINTER(structs.Register)]
        res = self.dll_target.target_write_cpu_reg(self.tgt, ctypes.byref(rn))
        return True if not res else False
    
    @open_required
    def read_cpu_reg(self, reg_index):
        """Read cpu register
       
        Args:
          self (CKLink): the ``CKLink`` instance
          reg_index (int): reigster to read from
          
        Returns:
          The value (int) stored in the given register
        """
        rn = structs.Register()
        rn.num = reg_index
        res = self.dll_target.target_read_cpu_reg(self.tgt, ctypes.byref(rn))
        if not res:
            return rn.value.val32
        else:
            raise errors.CKLinkException('Read cpu register failed')
    
    @open_required
    def add_soft_breakpoint(self, addr, length=2):
        """Sets a soft breakpoint at the specified address

        Args:
          self (CKLink): the ``CKLink`` instance
          addr (int): the address where the breakpoint will be set
          length (int): the breakpoint length, it could be 2 or 4

        Returns:
          ``True`` if success, ``False`` otherwise
        """
        res = self.dll_target.breakpoint_add(self.tgt, addr, length, 0)
        return True if not res else False
    
    @open_required
    def add_hard_breakpoint(self, addr, length=2):
        """Sets a hard breakpoint at the specified address

        Args:
          self (CKLink): the ``CKLink`` instance
          addr (int): the address where the breakpoint will be set
          length (int): the breakpoint length, it could be 2 or 4

        Returns:
          ``True`` if success, ``False`` otherwise
        """
        res = self.dll_target.breakpoint_add(self.tgt, addr, length, 1)
        return True if not res else False
    
    @open_required          
    def clear_breakpoint(self):
        res = self.dll_target.breakpoint_clear(self.tgt)
        return True if not res else False
    
    @open_required          
    def enable_ddc(self):
        res = self.dll_target.target_enable_ddc(self.tgt, 1)
        return True if not res else False 
    
    @open_required
    def disable_ddc(self):
        res = self.dll_target.target_enable_ddc(self.tgt, 0)
        return True if not res else False
    
    @open_required
    def single_step(self):
        res = self.dll_target.target_single_step(self.tgt)
        return True if not res else False
    
    @open_required
    def enable_cache_flush(self):
        res = self.dll_target.target_enable_cache_flush(self.tgt, 1)
        return True if not res else False
    
    @open_required
    def disable_cache_flush(self):
        res = self.dll_target.target_enable_cache_flush(self.tgt, 0)
        return True if not res else False

    











