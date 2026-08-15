from __future__ import annotations

PERMISSIONS = {
    "linux": [
        {"feature":"System/network/storage","default":"user","elevation":"not required"},
        {"feature":"journalctl error logs","default":"user/group-dependent","elevation":"may be required"},
        {"feature":"failed login history","default":"restricted","elevation":"may be required"},
        {"feature":"Docker diagnostics","default":"docker-socket access","elevation":"do not use sudo automatically"},
    ],
    "windows": [
        {"feature":"System/network/volumes","default":"standard user","elevation":"not required"},
        {"feature":"System Event Log","default":"standard user","elevation":"some channels may require Administrator"},
        {"feature":"Defender status","default":"standard user","elevation":"policy-dependent"},
        {"feature":"Local Administrators listing","default":"standard user","elevation":"policy-dependent"},
    ],
    "macos": [
        {"feature":"System/network/storage","default":"standard user","elevation":"not required"},
        {"feature":"Unified Log","default":"standard user","elevation":"some records may be restricted"},
        {"feature":"FileVault/SIP/Gatekeeper status","default":"standard user","elevation":"not required for status queries"},
    ],
}

def get_permissions(platform_name: str):
    return list(PERMISSIONS.get(platform_name, []))
