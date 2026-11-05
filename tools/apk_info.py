"""
tools/apk_info.py - Bóc "danh sách API" từ file APK: quyền, component,
SDK, thư viện native, các SDK third-party.

Chạy:  python tools/apk_info.py <duong_dan_file.apk> [ten_file_out.json]
Ví dụ: python tools/apk_info.py apk_work/hayday.apk apk_work/api_list.json
"""

import json
import os
import sys
import zipfile

from androguard.core.apk import APK


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    apk_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.splitext(apk_path)[0] + "_api.json"

    a = APK(apk_path)
    info = {
        "file": os.path.basename(apk_path),
        "size_bytes": os.path.getsize(apk_path),
        "package": a.get_package(),
        "app_name": a.get_app_name(),
        "version_name": a.get_androidversion_name(),
        "version_code": a.get_androidversion_code(),
        "min_sdk": a.get_min_sdk_version(),
        "target_sdk": a.get_target_sdk_version(),
        "max_sdk": a.get_max_sdk_version(),

        # ---- Quyền (Android Permission API) ---- #
        "permissions_requested": sorted(a.get_permissions()),
        "permission_groups": sorted(a.get_groups()),

        # ---- Component (entry point của app - API surface) ---- #
        "activities": sorted(a.get_activities()),
        "services": sorted(a.get_services()),
        "receivers": sorted(a.get_receivers()),
        "providers": sorted(a.get_providers()),
        "main_activity": a.get_main_activity(),

        # ---- Metadata ---- #
        "meta_data": {k: v for k, v in (a.get_meta_data() or {}).items()},

        # ---- Native libraries ---- #
        "native_libs_abi": sorted(a.get_libraries()),

        # ---- Thiết bị/API yêu cầu ---- #
        "uses_feature": a.get_features(),
        "uses_configuration": a.get_uses_configuration(),
    }

    # SDK third-party nhận diện từ package Java trong dex (quét tên nhãn lớn)
    third_party_markers = {
        "firebase", "facebook", "applovin", "adcolony", "unity", "ironsource",
        "vungle", "appsflyer", "adjust", "chartboost", "flurry", "crashlytics",
        "google", "play", "supercell", "scillm", "helpshift", "tenjin",
    }
    found = set()
    try:
        for s in a.get_services() + a.get_receivers() + a.get_activities() \
                + a.get_providers():
            low = s.lower()
            for mk in third_party_markers:
                if mk in low:
                    found.add(mk)
    except Exception:
        pass
    # quét thêm dex strings nhanh (1MB đầu mỗi dex)
    try:
        with zipfile.ZipFile(apk_path) as z:
            for name in z.namelist():
                if name.startswith("classes") and name.endswith(".dex"):
                    blob = z.read(name)[:2_000_000].decode("latin-1", "ignore")
                    for mk in third_party_markers:
                        if ("Lcom/" + mk) in blob.lower():
                            found.add(mk)
    except Exception:
        pass
    info["third_party_sdks_detected"] = sorted(found)

    # native libs chi tiết
    try:
        with zipfile.ZipFile(apk_path) as z:
            libs = sorted({os.path.basename(p) for p in z.namelist()
                           if p.startswith("lib/") and p.endswith(".so")})
        info["native_libs_files"] = libs
    except Exception:
        info["native_libs_files"] = []

    text = json.dumps(info, ensure_ascii=False, indent=2)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Package        : {info['package']}")
    print(f"Tên            : {info['app_name']}")
    print(f"Phiên bản      : {info['version_name']} (code {info['version_code']})")
    print(f"SDK            : min {info['min_sdk']} / target {info['target_sdk']}")
    print(f"Quyền ({len(info['permissions_requested'])}):")
    for p in info["permissions_requested"]:
        print(f"  - {p}")
    print(f"Activities ({len(info['activities'])}), Services "
          f"({len(info['services'])}), Receivers ({len(info['receivers'])}), "
          f"Providers ({len(info['providers'])})")
    print(f"Main activity  : {info['main_activity']}")
    print(f"Native ABI     : {info['native_libs_abi']}")
    print(f"SDK nhận diện  : {info['third_party_sdks_detected']}")
    print(f"\nJSON đầy đủ: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
