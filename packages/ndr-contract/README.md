# Sunbeam NDR placement contract

`sunbeam_ndr_contract` defines the v1 placement payload exchanged by the
network-agents charm and snap. Use `parse_instances()` to validate decoded
placement JSON, including attachment names, VLANs and addresses. Parsed
attachments are represented by `ProviderTrunk` and `DedicatedUplink`. The
snap enables legacy identity-only parsing when it reads saved configuration.

The package has no runtime dependencies. Live peering checks belong to the
snap, and Netplan ownership checks belong to the charm.
