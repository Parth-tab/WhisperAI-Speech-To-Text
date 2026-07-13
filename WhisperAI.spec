# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Collect all llama_cpp assets up-front so we can merge them into Analysis
llama_datas, llama_binaries, llama_hiddenimports = collect_all('llama_cpp')
fw_datas, fw_binaries, fw_hiddenimports = collect_all('faster_whisper')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=llama_binaries + fw_binaries,
    datas=[('models', 'models'), ('resources', 'resources')] + llama_datas + fw_datas,
    hiddenimports=llama_hiddenimports + fw_hiddenimports,
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['rthooks/rthook_llama_cpp.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WhisperAI',
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
