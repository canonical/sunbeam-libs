# SPDX-FileCopyrightText: 2026 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

"""Wire types and placement validation for the NDR host interface."""

import ipaddress
import re
from dataclasses import dataclass
from typing import Final, Literal, TypedDict

CONTRACT_VERSION: Final = 1
_INSTANCE_FIELDS = {"domain", "family", "service-name", "host", "router-id", "peering"}
_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_DEVICE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,14}")
_PHYSNET = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")
_HOST = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?")

ValidationResult = TypedDict(
    "ValidationResult",
    {
        "contract-version": Literal[1],
        "instances": list[dict[str, object]],
        "managed-addresses": dict[str, str],
    },
)


@dataclass(frozen=True)
class Agent:
    service: str
    host: str
    router_id: str
    domain: str = ""


@dataclass(frozen=True)
class ProviderTrunk:
    """A provider network segment and the address to configure on it."""

    physnet: str
    vlan: int
    address: ipaddress.IPv4Interface | ipaddress.IPv6Interface


@dataclass(frozen=True)
class DedicatedUplink:
    """An existing uplink and the optional address it must already have."""

    interface: str
    address: ipaddress.IPv4Address | ipaddress.IPv6Address | None


PeeringSpec = ProviderTrunk | DedicatedUplink


@dataclass(frozen=True)
class Instance:
    """Validated agent identity and its wire-format peering declaration."""

    agent: Agent
    ip_version: Literal[4, 6]
    peering: PeeringSpec | None
    declaration: dict[str, object]


def parse_instances(
    instances: object, *, allow_legacy: bool = False
) -> tuple[Instance, ...]:
    """Validate the placement list without reading host state.

    Allow identity-only entries when loading saved snap configuration that
    predates peering declarations.
    """
    if not isinstance(instances, list):
        raise TypeError("NDR configuration must contain an instances list.")
    placement: list[Instance] = []
    services: set[str] = set()
    hosts: set[str] = set()
    router_ids: set[str] = set()
    peered_domains: set[str] = set()
    for instance in instances:
        if not isinstance(instance, dict) or instance.get("family") not in (
            "ipv4",
            "ipv6",
        ):
            raise ValueError(
                "NDR agent instances must use the ipv4 or ipv6 address family."
            )
        if instance.keys() - _INSTANCE_FIELDS:
            raise ValueError("NDR agent instance contains unsupported fields.")
        domain = instance.get("domain")
        service = instance.get("service-name")
        host = instance.get("host")
        router_id = instance.get("router-id")
        if not (
            isinstance(domain, str)
            and len(domain) <= 255
            and _NAME.fullmatch(domain)
            and isinstance(service, str)
            and len(service) <= 255
            and _NAME.fullmatch(service)
            and isinstance(host, str)
            and len(host) <= 255
            and _HOST.fullmatch(host)
            and isinstance(router_id, str)
        ):
            raise ValueError("NDR agent instance contains an invalid identity.")
        try:
            address = ipaddress.IPv4Address(router_id)
        except ipaddress.AddressValueError:
            raise ValueError("NDR router ID must be an IPv4 address.") from None
        if address.is_unspecified or address.is_multicast:
            raise ValueError("NDR router ID must be a nonzero unicast IPv4 address.")
        if service in services or host in hosts or router_id in router_ids:
            raise ValueError(
                "NDR service names, host identities and router IDs must be unique."
            )
        services.add(service)
        hosts.add(host)
        router_ids.add(router_id)
        ip_version: Literal[4, 6] = 4 if instance["family"] == "ipv4" else 6
        peering = None
        if "peering" in instance:
            peering = _parse_peering(domain, ip_version, instance["peering"])
            if domain in peered_domains:
                raise ValueError(f"Duplicate NDR domain {domain} on this node.")
            peered_domains.add(domain)
        elif not allow_legacy:
            raise ValueError(
                f"NDR domain {domain} needs exactly one peering attachment."
            )
        placement.append(
            Instance(
                Agent(service, host, router_id, domain), ip_version, peering, instance
            )
        )
    return tuple(placement)


def _parse_peering(domain: str, family: int, raw: object) -> PeeringSpec:
    if not isinstance(raw, dict) or len(raw) != 1:
        raise ValueError(f"NDR domain {domain} needs exactly one peering attachment.")
    kind, options = next(iter(raw.items()))
    if kind not in ("dedicated-uplink", "provider-trunk"):
        raise ValueError(f"Unsupported NDR attachment mode for {domain}.")
    if not isinstance(options, dict):
        raise TypeError(f"Invalid NDR peering attachment for {domain}.")
    if kind == "provider-trunk":
        return _parse_provider_trunk(family, options)
    return _parse_dedicated_uplink(family, options)


def is_usable_peering_address(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    """Return whether an address is suitable for a BGP peering attachment."""
    return not (
        address.is_link_local
        or address.is_loopback
        or address.is_multicast
        or address.is_unspecified
    )


def _parse_provider_trunk(family: int, options: dict[str, object]) -> ProviderTrunk:
    if options.keys() != {"physnet", "vlan", "address"}:
        raise ValueError("provider-trunk requires physnet, vlan and address.")
    physnet = options["physnet"]
    vlan = options["vlan"]
    if (
        not isinstance(physnet, str)
        or not _PHYSNET.fullmatch(physnet)
        or type(vlan) is not int
        or not 1 <= vlan <= 4094
    ):
        raise ValueError("Invalid NDR physnet or peering VLAN.")
    value = options["address"]
    if not isinstance(value, str) or "/" not in value:
        raise ValueError("NDR provider-trunk address must be a CIDR.")
    address = ipaddress.ip_interface(value)
    if address.version != family or not is_usable_peering_address(address.ip):
        raise ValueError(
            "NDR provider-trunk address must match the family and be usable."
        )
    return ProviderTrunk(physnet, vlan, address)


def _parse_dedicated_uplink(family: int, options: dict[str, object]) -> DedicatedUplink:
    if "interface" not in options or options.keys() - {"interface", "address"}:
        raise ValueError("dedicated-uplink requires an interface and optional address.")
    interface = options["interface"]
    if not isinstance(interface, str) or not _DEVICE.fullmatch(interface):
        raise ValueError("Invalid NDR dedicated interface name.")
    value = options.get("address")
    if value is None:
        return DedicatedUplink(interface, None)
    if not isinstance(value, str):
        raise TypeError("NDR dedicated address must be a bare IP address.")
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        raise ValueError("NDR dedicated address must be a bare IP address.") from None
    if address.version != family or not is_usable_peering_address(address):
        raise ValueError("NDR dedicated address must match the family and be usable.")
    return DedicatedUplink(interface, address)
