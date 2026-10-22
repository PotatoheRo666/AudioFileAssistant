import sys
import os
import ctypes

if sys.platform == 'win32':
    for dll in ['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll']:
        try:
            loaded = False
            if hasattr(sys, '_MEIPASS'):
                p = os.path.join(sys._MEIPASS, dll)
                if os.path.exists(p):
                    ctypes.CDLL(p)
                    loaded = True
            if not loaded:
                sys_dll = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', dll)
                if os.path.exists(sys_dll):
                    ctypes.CDLL(sys_dll)
        except Exception:
            pass
