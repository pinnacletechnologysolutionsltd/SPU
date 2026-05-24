# -*- coding:utf-8 -*-


import ctypes

fn1_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char)
fn2_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p)


class ValueOfReg(ctypes.Union): 
    _fields_ = [
        ("val8", ctypes.c_ubyte),
        ("val16", ctypes.c_ushort),  
        ("val32", ctypes.c_uint),
        ("val64", ctypes.c_uint64),  
        ("valf", ctypes.c_float),
        ("vald", ctypes.c_double), 
        ('raw', ctypes.c_ubyte * 16),     
    ]


class Register(ctypes.Structure):
    """Register info structure.

    Attributes:

    """
    _fields_ = [
        ('name', ctypes.c_char * 32),    # Name of register
        ('num', ctypes.c_int),           # Register number
        ('type', ctypes.c_int),          # Register type
        ('length', ctypes.c_int),        # Register length
        ('value', ValueOfReg),
    ]


class LinkDevice(ctypes.Structure):
    """Link device info structure.

    Attributes:

    """
    _fields_ = [
        ('device', ctypes.c_void_p),
        ('handler', ctypes.c_void_p),
        ('vid', ctypes.c_int),
        ('pid', ctypes.c_int),
        ('bcdDevice', ctypes.c_int),
        ('dev_str', ctypes.c_char * 200),
        ('sn', ctypes.c_char * 200),
        ('state', ctypes.c_int),
    ]


class LinkCfg(ctypes.Structure):
    """Link Cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('vid', ctypes.c_ushort),
        ('pid', ctypes.c_ushort),
        ('root_path', ctypes.c_char_p), # Program root path
        ('mtcr_delay', ctypes.c_int),   # MTCR instruction write delay. arch.cache_flush_delay will replace this
        ('cdi', ctypes.c_int),          # JTAG/SWD select, JTAG=0, SWD=1
        ('nrst_delay', ctypes.c_int),   # NRESET Pin hold time while do nreset
        ('trst_delay', ctypes.c_int),   # TRESET pin hold time while do nreset
        ('trst_en', ctypes.c_ubyte),    # Do TRESET while do reset. It should be always true
        ('ice_clk', ctypes.c_uint),     # Link TCLK Clock
        ('serial', ctypes.c_char_p),    # Serail number for the target. If set, connect the device with the SN
        ('config_path', ctypes.c_char_p)# The Firmware config path
    ]
    
#     def __init__(self):
#         self.vid = int("42bf", 16)
#         self.pid = int("b210", 16)
#         self.root_path = ctypes.c_char_p("root_path".encode())
#         self.cdi = 0
#         self.nrst_delay = 100
#         self.trst_delay = 110
#         self.trst_en = 1
#         self.ice_clk = 12000
#         #self.serial = ctypes.c_char_p("sn".encode())
#         #self.config_path = ctypes.c_char_p("config".encode())


class MiscCfg(ctypes.Structure):
    """Misc cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('verbose', ctypes.c_int),            # Log Level config
        ('print_version', ctypes.c_int),      # Print DebugServer Version info
        ('msgout', fn2_type),                 # Message output interface
        ('errout', fn2_type),                 # Error output interface
        ('return_after_ice_connection', ctypes.c_ubyte), # Don't check target while connectint
    ]

   
class ArchCfg(ctypes.Structure):
    """Arch Cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('debug_arch', ctypes.c_int),             # Debug architecture 0:none, 1:csky, 2:riscv, 3:auto
        ('no_cpuid_check', ctypes.c_uint),        # Do not check cpuid while connectting
        ('isa_version', ctypes.c_int),            # ISA version for T-HEAD  
        ('hacr_width', ctypes.c_int),             # HACR length in bits
        ('tdesc_xml_file', ctypes.c_char_p),      # The register xml file path
        ('script', ctypes.c_char_p),              # Jtag or GPIO Script file path. Exit after executing script
        ('target_init_script', ctypes.c_char_p),  # Jtag or GPIO Script file path.  Continue after executing script
        ('pre_reset', ctypes.c_ubyte),            # Do prerest before connecting
        ('no_cache_flush', ctypes.c_ubyte),       # Don't flush cache
        ('cache_flush_delay', ctypes.c_uint),     # Delay for doing flush caches
        ('rst_sleep', ctypes.c_int),              # Wait for target system set-up
        ('idle_delay', ctypes.c_uint),            # idle_delay for riscv...
        ('ndmrst_delay', ctypes.c_uint),          # Set delay time for DMCONTROL.cmdreset signal
        ('hartrst_delay', ctypes.c_uint),         # Set delay time for DMCONTROL.hartreset signal
    ]
    
#     def __init__(self):
#         self.debug_arch = 3


class SocketCfg(ctypes.Structure):
    """Socket cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('onlyserver', ctypes.c_ubyte),  # Only start server, not force cpu into debu mode
        ('port', ctypes.c_int),          # Socket port for remote server
        ('is_multicore_threads', ctypes.c_ubyte), # Only one port for SMP
    ]
    
#     def __init__(self):
#         self.onlyserver = 0 # False
#         self.port = 1025
#         self.is_multicore_threads = 1 # True
    

class DcommCfg(ctypes.Structure):
    """Dcomm cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('type', ctypes.c_int),
        ('on_target_stdout', fn1_type),
        ('on_remote_stdout', fn1_type),
    ]


class DsamplingCfg(ctypes.Structure):
    """Dsampling cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('sampling', ctypes.c_int),
        ('sampling_freq', ctypes.c_uint),
        ('sampling_port', ctypes.c_int),
        ('sampling_cpu', ctypes.c_uint),
        ('type', ctypes.c_int),
    ]
    

class FunctionalCfg(ctypes.Structure):
    """Functional Cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('ddc_flag', ctypes.c_ubyte),          # Enale write memory via DDC
        ('local_semi', ctypes.c_ubyte),        # Do semihosting in DebugServer or not
        ('cmdline_en', ctypes.c_ubyte),        # Enable CommandLine
        ('cmd_script_path', ctypes.c_char_p),  # Command Line initial script path
        ('speeded_up', ctypes.c_int),          # Operations of accessing memory and register in cklink
        ('dcomm', DcommCfg),                   # Debug Comunications(Debug-Print)
        ('dsampling', DsamplingCfg),           # Debug Sampling(PC, ContextID)
    ]


class Target(ctypes.Structure):
    pass


class DebuggerDerverCfg(ctypes.Structure):
    """Debugger Derver Cfg info structure.

    Attributes:

    """
    _fields_ = [
        ('priv', ctypes.c_void_p), # Private data
        ('root_path', ctypes.c_char_p), # Program root path
        ('ide_flag', ctypes.c_uint),
        ('do_link_upgrade', ctypes.c_uint),
        ('link', LinkCfg), # ICE config
        ('misc', MiscCfg), # Misc config
        ('arch', ArchCfg), # architecture config
        ('socket', SocketCfg), # socket config
        ('function', FunctionalCfg), # functional config
        ('target', Target), # target config
        ('list_ice', ctypes.c_int), # List links
        ('list_vendor', ctypes.c_uint), # list vendor link
        ('vendor_name', ctypes.c_char_p), # select vendor link
        ('log_file_name', ctypes.c_char_p), # log file name
    ]
    

        


