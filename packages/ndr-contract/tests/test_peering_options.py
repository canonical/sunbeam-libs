# SPDX-FileCopyrightText: 2026 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

import pytest
from sunbeam_ndr_contract import parse_instances


@pytest.mark.parametrize(
    ("mode", "options", "message"),
    [
        ("provider-trunk", {"vlan": 120}, "requires physnet, vlan and address"),
        (
            "provider-trunk",
            {"physnet": 123, "vlan": 120, "address": "192.0.2.3/28"},
            "Invalid NDR physnet or peering VLAN",
        ),
        (
            "provider-trunk",
            {"physnet": "physnet1", "vlan": True, "address": "192.0.2.3/28"},
            "Invalid NDR physnet or peering VLAN",
        ),
        (
            "provider-trunk",
            {"physnet": "physnet1", "vlan": 4095, "address": "192.0.2.3/28"},
            "Invalid NDR physnet or peering VLAN",
        ),
        (
            "provider-trunk",
            {"physnet": "physnet1", "vlan": 120, "address": "192.0.2.3"},
            "address must be a CIDR",
        ),
        (
            "provider-trunk",
            {"physnet": "physnet1", "vlan": 120, "address": "2001:db8::3/64"},
            "address must match the family and be usable",
        ),
        (
            "provider-trunk",
            {"physnet": "physnet1", "vlan": 120, "address": "169.254.0.1/24"},
            "address must match the family and be usable",
        ),
        (
            "dedicated-uplink",
            {"interface": "uplink0", "extra": False},
            "requires an interface and optional address",
        ),
        (
            "dedicated-uplink",
            {"interface": "../bad"},
            "Invalid NDR dedicated interface",
        ),
        (
            "dedicated-uplink",
            {"interface": "uplink0", "address": "192.0.2.3/28"},
            "address must be a bare IP address",
        ),
        (
            "dedicated-uplink",
            {"interface": "uplink0", "address": "224.0.0.3"},
            "address must match the family and be usable",
        ),
    ],
)
def test_validate_peering_options_without_host_access(mode, options, message):
    placement = [
        {
            "domain": "red",
            "family": "ipv4",
            "host": "net-01.red",
            "service-name": "agent-red",
            "router-id": "198.18.0.1",
            "peering": {mode: options},
        }
    ]

    with pytest.raises(ValueError, match=message):
        parse_instances(placement, allow_legacy=True)
