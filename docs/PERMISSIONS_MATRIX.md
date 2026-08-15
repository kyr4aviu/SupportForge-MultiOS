# Permissions Matrix

SupportForge does not automatically elevate privileges.

| Platform | Diagnostic area | Normal context | Elevation |
|---|---|---|---|
| Linux | system/network/storage | user | not normally required |
| Linux | journal logs | user/group dependent | may be required by distro policy |
| Linux | failed-login history | restricted | may be required |
| Linux | Docker | docker socket membership/access | never auto-sudo |
| Windows | system/network/volumes | standard user | not normally required |
| Windows | Event Log | standard user | some channels may require Administrator |
| Windows | Defender/security state | standard user | policy dependent |
| macOS | system/network/storage | standard user | not normally required |
| macOS | Unified Log | standard user | some records may be restricted |
| macOS | FileVault/SIP/Gatekeeper status | standard user | status queries normally do not require elevation |

## Security rule

If a collector cannot read a source with the current token, SupportForge records
the source as unavailable/restricted. It does not silently request elevation and
does not weaken host security controls.
