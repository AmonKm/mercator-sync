from .vcenter import VCenterConnector
from .xoa     import XoaConnector
from .proxmox import ProxmoxConnector

REGISTRY: dict[str, type] = {
    "vcenter": VCenterConnector,
    "xoa":     XoaConnector,
    "proxmox": ProxmoxConnector
}
