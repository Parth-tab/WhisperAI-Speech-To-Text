# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, copy_metadata

binaries_list = []
binaries_list += collect_dynamic_libs('llama_cpp')
binaries_list += collect_dynamic_libs('ctranslate2')
binaries_list += collect_dynamic_libs('sounddevice')

datas_list = []
datas_list += collect_data_files('llama_cpp')
datas_list += collect_data_files('faster_whisper')
datas_list += collect_data_files('sounddevice')
for pkg in ['tqdm', 'regex', 'huggingface-hub']:
    try:
        datas_list += copy_metadata(pkg)
    except Exception:
        pass

datas_list += [('src/assets/branding/*', 'src/assets/branding')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_list,
    datas=datas_list,
    hiddenimports=['llama_cpp', 'faster_whisper', 'ctranslate2', 'tiktoken_ext.openai_public', 'tiktoken_ext'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

splash = Splash(
    'src/assets/branding/logo.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=True,
    max_img_size=(1024, 1024)
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    splash.binaries,
    [],
    name='WhisperAI',
    version='version.txt',
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
    icon=None,
)
