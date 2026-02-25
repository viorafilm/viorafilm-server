from copy import deepcopy
from typing import Any

from core.models import Device

from .models import ConfigProfile


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _latest_profile(scope: str, **filters) -> ConfigProfile | None:
    return (
        ConfigProfile.objects.filter(scope=scope, **filters)
        .order_by("-version", "-updated_at", "-id")
        .first()
    )


def get_effective_config(device: Device) -> tuple[dict[str, Any], str]:
    global_profile = _latest_profile(
        ConfigProfile.SCOPE_GLOBAL,
        org__isnull=True,
        branch__isnull=True,
        device__isnull=True,
    )
    org_profile = _latest_profile(
        ConfigProfile.SCOPE_ORG,
        org=device.org,
        branch__isnull=True,
        device__isnull=True,
    )
    branch_profile = _latest_profile(
        ConfigProfile.SCOPE_BRANCH,
        branch=device.branch,
        device__isnull=True,
    )
    device_profile = _latest_profile(
        ConfigProfile.SCOPE_DEVICE,
        device=device,
    )

    effective: dict[str, Any] = {}
    for profile in (global_profile, org_profile, branch_profile, device_profile):
        if profile and isinstance(profile.payload, dict):
            effective = _deep_merge(effective, profile.payload)

    gv = int(global_profile.version) if global_profile and global_profile.version else 0
    ov = int(org_profile.version) if org_profile and org_profile.version else 0
    bv = int(branch_profile.version) if branch_profile and branch_profile.version else 0
    dv = int(device_profile.version) if device_profile and device_profile.version else 0
    version_tag = f"g{gv}-o{ov}-b{bv}-d{dv}"
    return effective, version_tag
