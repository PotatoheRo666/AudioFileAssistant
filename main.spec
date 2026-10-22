# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import onnxruntime
from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = []
binaries += collect_dynamic_libs('imageio_ffmpeg')

datas = []
ort_dir = os.path.dirname(onnxruntime.__file__)
datas.append((ort_dir, 'onnxruntime'))

if os.path.exists('models'):
    datas.append(('models', 'models'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rth_preload_crt.py'],
    excludes=['onnxruntime', 'scipy'],
    noarchive=False,
    optimize=0,
)

# 1. 过滤掉 PyQt5 自带的旧版 MSVC CRT DLL (v14.26)，该旧版 DLL 与 onnxruntime 冲突会导致 0xC0000005 崩溃
filtered_binaries = []
for dest, src, typ in a.binaries:
    dest_lower = dest.lower()
    if 'pyqt5' in dest_lower and ('msvcp140' in dest_lower or 'vcruntime140' in dest_lower):
        continue
    filtered_binaries.append((dest, src, typ))

# 2. 注入系统最新现代 C++ 运行时 (v14.51+) 到根目录以及 PyQt5/Qt5/bin 目录中
sys32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')
crt_dlls = ['msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'vcruntime140.dll', 'vcruntime140_1.dll']
for dll in crt_dlls:
    src = os.path.join(sys32, dll)
    if os.path.exists(src):
        filtered_binaries.append((dll, src, 'BINARY'))
        filtered_binaries.append((os.path.join('PyQt5', 'Qt5', 'bin', dll), src, 'BINARY'))

a.binaries = filtered_binaries

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
