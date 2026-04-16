"""
C++ Bridge for LTE IQ Analysis
Provides a Python interface to the high-performance C++ engine.
"""
import ctypes
import os
import numpy as np
import platform

class PssRawResults(ctypes.Structure):
    _fields_ = [
        ("max_correlation", ctypes.c_double),
        ("max_correlation_pss0", ctypes.c_double),
        ("max_correlation_pss1", ctypes.c_double),
        ("max_correlation_pss2", ctypes.c_double),
        ("max_correlation_index", ctypes.c_int),
        ("max_correlation_position", ctypes.c_int),
        ("frequency_offset", ctypes.c_double),
        ("pss_start", ctypes.c_int),
    ]

# Path to the shared library
LIB_NAME = "lte_engine.dll" if platform.system() == "Windows" else "liblte_engine.so"
LIB_PATH = os.path.join(os.path.dirname(__file__), "cpp", "build", LIB_NAME)

_lib = None

def load_lib():
    global _lib
    if _lib is not None:
        return _lib
    
    if not os.path.exists(LIB_PATH):
        return None
    
    try:
        _lib = ctypes.CDLL(LIB_PATH)
        _lib.lte_detect_pss.argtypes = [
            ctypes.POINTER(ctypes.c_float), # iq_real
            ctypes.POINTER(ctypes.c_float), # iq_imag
            ctypes.c_int, # num_samples
            ctypes.c_int, # fft_bin_size
            ctypes.c_double # sample_rate
        ]
        _lib.lte_detect_pss.restype = PssRawResults
        return _lib
    except Exception as e:
        print(f"Error loading C++ library: {e}")
        return None

def detect_pss_cpp(iq_samples, fft_bin_size=2048, sample_rate=30.72e6):
    """
    Calls the C++ engine to perform PSS detection.
    """
    lib = load_lib()
    if lib is None:
        raise RuntimeError("C++ library not built or loaded. Run build first.")
    
    iq_real = iq_samples.real.astype(np.float32)
    iq_imag = iq_samples.imag.astype(np.float32)
    
    num_samples = len(iq_samples)
    
    # Get pointers to numpy data
    p_real = iq_real.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    p_imag = iq_imag.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    
    # Call C++
    res = lib.lte_detect_pss(p_real, p_imag, num_samples, fft_bin_size, sample_rate)
    
    # Convert ctypes result to dictionary compatible with existing Python code
    return {
        'max_correlation': res.max_correlation,
        'max_correlation_pss0': res.max_correlation_pss0,
        'max_correlation_pss1': res.max_correlation_pss1,
        'max_correlation_pss2': res.max_correlation_pss2,
        'max_correlation_index': res.max_correlation_index,
        'max_correlation_position': res.max_correlation_position,
        'frequency_offset': res.frequency_offset,
        'pss_start': res.pss_start,
        # ofdm_symbols and other derived data are still handled in Python for now
    }

def is_cpp_available():
    return os.path.exists(LIB_PATH)
