# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['lif-dat_main.py'],
             pathex=['C:\\Users\\jdcoh\\PycharmProjects\\LIF-DAT'],
             binaries=[],
             datas=[('laser_logo.jpg', 'laser_logo.jpg')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='LIF-DAT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='laser_logo.ico')
