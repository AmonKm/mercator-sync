from .vcenter import VCenterConnector
from .xoa     import XoaConnector

REGISTRY: dict[str, type] = {
    "vcenter": VCenterConnector,
    "xoa":     XoaConnector,
}
# à commenter !
