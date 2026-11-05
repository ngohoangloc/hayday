#!/usr/bin/env python3
"""Batch-decode SuperCell SC/SCTX atlas groups thành PNG."""
import os, sys, traceback
from pathlib import Path

os.environ["HOME"] = os.path.abspath("apk_work/.home")
os.makedirs("apk_work/.home/.cache", exist_ok=True)

from mb_sc_tools import decode_file

SRC = Path("apk_work/xapk/extracted/assets/sc")
OUT = Path("apk_work/decoded")

GROUPS = sys.argv[1:] or ["icons", "hud", "hud_roadside_shop", "hud_inventory",
                          "nature_new", "hud_money_shop", "common",
                          "hud_order_board", "hud_context_menus"]

def main():
    for g in GROUPS:
        d = OUT / g
        d.mkdir(parents=True, exist_ok=True)
        for f in sorted(SRC.glob(f"{g}.sc")) + sorted(SRC.glob(f"{g}_*.sctx")) + \
                 sorted(SRC.glob(f"{g}.sctx")):
            try:
                r = decode_file(f, d)
                kind = r.get("kind", "?")
                if kind == "sctx":
                    print(f"{f.name}: {r.get('type')} {r.get('width')}x{r.get('height')}")
                else:
                    texs = r.get("textures") or []
                    print(f"{f.name}: SWF, {len(texs)} texture refs")
            except Exception as e:
                print(f"{f.name}: FAIL {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
