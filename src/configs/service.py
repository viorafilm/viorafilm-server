from typing import Any, Dict, Tuple

from core.models import Device

from .models import ConfigProfile, ConfigScope


def _latest(scope: str, **kwargs):
    return ConfigProfile.objects.filter(scope=scope, **kwargs).order_by("-version").first()


def get_effective_config(device: Device) -> Tuple[Dict[str, Any], str]:
    g = _latest(ConfigScope.GLOBAL, org=None, branch=None, device=None)
    o = _latest(ConfigScope.ORG, org=device.org)
    b = _latest(ConfigScope.BRANCH, branch=device.branch)
    d = _latest(ConfigScope.DEVICE, device=device)

    cfg: Dict[str, Any] = {}
    if g:
        cfg.update(g.payload or {})
    if o:
        cfg.update(o.payload or {})
    if b:
        cfg.update(b.payload or {})
    if d:
        cfg.update(d.payload or {})

    gv = g.version if g else 0
    ov = o.version if o else 0
    bv = b.version if b else 0
    dv = d.version if d else 0
    version_tag = f"g{gv}-o{ov}-b{bv}-d{dv}"
    return cfg, version_tag

