# SPDX-FileCopyrightText: 2026 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

from ipaddress import IPv4Interface, IPv6Address

import pytest
from sunbeam_ndr_contract import Agent, DedicatedUplink, ProviderTrunk, parse_instances


def test_parse_v1_placement():
    declaration = {
        "domain": "blue",
        "family": "ipv6",
        "service-name": "agent-blue-v6",
        "host": "net-01.blue.v6",
        "router-id": "198.18.0.1",
        "peering": {
            "dedicated-uplink": {"interface": "uplink0", "address": "2001:db8::3"},
        },
    }

    (instance,) = parse_instances([declaration])

    assert instance.agent == Agent(
        "agent-blue-v6", "net-01.blue.v6", "198.18.0.1", "blue"
    )
    assert instance.ip_version == 6
    assert instance.peering == DedicatedUplink("uplink0", IPv6Address("2001:db8::3"))
    assert instance.declaration == declaration


def test_identity_only_requires_legacy_mode():
    declaration = {
        "domain": "red",
        "family": "ipv4",
        "service-name": "agent-red-v4",
        "host": "net-01.red.v4",
        "router-id": "198.18.0.1",
    }

    with pytest.raises(ValueError, match="needs exactly one peering attachment"):
        parse_instances([declaration])

    (instance,) = parse_instances([declaration], allow_legacy=True)
    assert instance.peering is None
    assert instance.declaration == declaration


@pytest.fixture
def placement() -> list[dict[str, object]]:
    return [
        {
            "domain": "red",
            "family": "ipv4",
            "service-name": "agent-red",
            "host": "net-01.red",
            "router-id": "198.18.0.1",
            "peering": {
                "provider-trunk": {
                    "physnet": "physnet1",
                    "vlan": 120,
                    "address": "192.0.2.3/28",
                },
            },
        },
        {
            "domain": "blue",
            "family": "ipv6",
            "service-name": "agent-blue",
            "host": "net-01.blue",
            "router-id": "198.18.0.2",
            "peering": {"dedicated-uplink": {"interface": "uplink122"}},
        },
    ]


def test_parse_distinct_domains_and_address_families(
    placement: list[dict[str, object]],
):
    red, blue = parse_instances(placement)

    assert (red.ip_version, blue.ip_version) == (4, 6)
    assert red.peering == ProviderTrunk("physnet1", 120, IPv4Interface("192.0.2.3/28"))
    assert blue.peering == DedicatedUplink("uplink122", None)
    assert (red.declaration, blue.declaration) == tuple(placement)


@pytest.mark.parametrize("field", ["service-name", "host", "router-id"])
def test_reject_duplicate_agent_identity(
    placement: list[dict[str, object]], field: str
):
    red, blue = placement
    blue[field] = red[field]

    with pytest.raises(ValueError, match="must be unique"):
        parse_instances(placement)


def test_reject_same_peered_domain_across_address_families(
    placement: list[dict[str, object]],
):
    placement[1]["domain"] = placement[0]["domain"]

    with pytest.raises(ValueError, match="Duplicate NDR domain red"):
        parse_instances(placement)


@pytest.mark.parametrize(
    ("router_id", "message"),
    [
        ("2001:db8::1", "must be an IPv4 address"),
        ("0.0.0.0", "must be a nonzero unicast IPv4 address"),
        ("224.0.0.1", "must be a nonzero unicast IPv4 address"),
    ],
)
def test_reject_invalid_router_id(
    placement: list[dict[str, object]], router_id: str, message: str
):
    placement[0]["router-id"] = router_id

    with pytest.raises(ValueError, match=message):
        parse_instances(placement)


@pytest.mark.parametrize(
    ("peering", "error", "message"),
    [
        ([], ValueError, "needs exactly one peering attachment"),
        ({}, ValueError, "needs exactly one peering attachment"),
        (
            {"provider-trunk": {}, "dedicated-uplink": {}},
            ValueError,
            "needs exactly one peering attachment",
        ),
        ({"other": {}}, ValueError, "Unsupported NDR attachment mode"),
        (
            {"dedicated-uplink": "uplink122"},
            TypeError,
            "Invalid NDR peering attachment",
        ),
    ],
)
def test_reject_malformed_peering_even_in_legacy_mode(
    placement: list[dict[str, object]],
    peering: object,
    error: type[Exception],
    message: str,
):
    placement[1]["peering"] = peering

    with pytest.raises(error, match=message):
        parse_instances(placement, allow_legacy=True)


def test_reject_unexpected_instance_field(placement: list[dict[str, object]]):
    placement[0]["provider-network"] = "public"

    with pytest.raises(ValueError, match="contains unsupported fields"):
        parse_instances(placement)


def test_domain_length_limit(placement: list[dict[str, object]]):
    placement[0]["domain"] = "a" * 255
    assert parse_instances(placement)[0].agent.domain == "a" * 255

    placement[0]["domain"] = "a" * 256
    with pytest.raises(ValueError, match="invalid identity"):
        parse_instances(placement)
