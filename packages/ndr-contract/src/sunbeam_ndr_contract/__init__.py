# SPDX-FileCopyrightText: 2026 - Canonical Ltd
# SPDX-License-Identifier: Apache-2.0

"""Placement contract shared by the Sunbeam snap and charm."""

from sunbeam_ndr_contract.placement import (
    CONTRACT_VERSION,
    Agent,
    DedicatedUplink,
    Instance,
    PeeringSpec,
    ProviderTrunk,
    ValidationResult,
    is_usable_peering_address,
    parse_instances,
)

__all__ = [
    "CONTRACT_VERSION",
    "Agent",
    "DedicatedUplink",
    "Instance",
    "PeeringSpec",
    "ProviderTrunk",
    "ValidationResult",
    "is_usable_peering_address",
    "parse_instances",
]
