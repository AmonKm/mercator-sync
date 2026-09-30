from typing import Literal, NotRequired, TypedDict
from typing import Any
JsonDict = dict[str, Any]
class VCenterAuth(TypedDict):
    username_env: str
    password_env: str

class VCenterConfig(TypedDict):
    type: Literal["vcenter"]
    name_id: str
    base_url: str
    auth: VCenterAuth
    verify_ssl: NotRequired[bool]
    enabled: NotRequired[bool]

class XOAAuth(TypedDict):
    username_env: str
    password_env: str
    token_env: str

class XOAConfig(TypedDict):
    type: Literal["xoa"]
    name_id: str
    base_url: str
    pool_id: str
    auth: XOAAuth
    verify_ssl: NotRequired[bool]
    enabled: NotRequired[bool]

class ProxmoxAuth(TypedDict):
    user_env: str
    token_env: str

class ProxmoxConfig(TypedDict):
    type: Literal["proxmox"]
    name_id: str
    base_url: str
    auth: ProxmoxAuth
    verify_ssl: NotRequired[bool]
    enabled: NotRequired[bool]

SourceConfig = VCenterConfig | ProxmoxConfig | XOAConfig