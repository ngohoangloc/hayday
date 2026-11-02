# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec cho HayDay Auto Bot.
# Build:  pyinstaller hayday-bot.spec
# Kết quả: dist/hayday-bot        (Linux)  |  dist/hayday-bot.exe  (Windows)

import os

SEP = ";" if os.name == "nt" else ":"

a = Analysis(
    ["run_bot.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("templates", "templates"),          # soil.jpg + template người dùng đặt kèm repo
        ("config.json", "."),
    ],
    hiddenimports=["sim", "soil"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="hayday-bot",
    debug=False,
    strip=False,
    upx=False,
    console=True,                            # bot chạy console, có log
)
