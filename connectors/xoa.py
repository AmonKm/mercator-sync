import os
import requests
from .base import BaseConnector


class XoaConnector(BaseConnector):

    def authenticate(self) -> None:
        token = os.environ[self.config["auth"]["token_env"]]
        self.cookies = {"authenticationToken": token}
        self.verify  = self.config.get("verify_ssl", True)
        self.base_url = os.environ[self.config["base_url"]]

    def fetch_clusters(self) -> list[dict]:
        pool_id = self.config["pool_id"]

        requête = requests.get(
            f"{self.base_url}/rest/v0/pools/{pool_id}",
            cookies=self.cookies, verify=self.verify
        )

        requête.raise_for_status()
        pool = requête.json()

        pool["id"] = pool_id  # s'assurer que l'id est présent à revoir

        return [pool]

    def fetch_vms(self, cluster_id: str) -> list[dict]: # Plusieurs appels si plusieurs clusters... A voir pour prendre une liste d'id de cluster ?
       requête= requests.get(
            f"{self.base_url}/rest/v0/vms",
            params={"filter": f"$pool:{cluster_id}", "fields": "id,name_label,power_state"},
            cookies=self.cookies, verify=self.verify
        )
       requête.raise_for_status()
       return requête.json()

    def enrich_vm(self, vm_id: str, _vm: dict) -> dict:
        requête= requests.get(
            f"{self.base_url}/rest/v0/vms/{vm_id}",
            cookies=self.cookies, verify=self.verify
        )
        requête.raise_for_status()
        return requête.json()

    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict:
        cpu     = enriched.get("CPUs", {}).get("number")
        mem_go  = round(enriched.get("memory", {}).get("size", 0) / (1024 ** 3), 1)
        os_info = enriched.get("os_version") or {}
        os_name = os_info.get("name", "")
        distro  = os_info.get("distro", "")
        tags    = enriched.get("tags", [])
        attributs = f"{self.name}"
        if distro:
            attributs += f" distro:{distro}"
        for tag in tags:
            attributs += f" {tag}"

        return {
            "name": enriched.get("name_label", "")[:32],
            "description":      f"VM importée de : {self.name} ({enriched['uuid']})<br>{enriched.get('name_description', '')}",
            "operating_system": os_name,
            "address_ip":       enriched.get("mainIpAddress", ""),
            "cpu":              cpu,
            "memory":           mem_go,
            "attributes":       attributs,
            "ext_refs": f"{{{self.name}}}{vm_id}", # on l'utilise enfin ! A voir pour ajouter de plusieurs sources...
        }
    
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        return {
            "name":       cluster.get("name_label", cluster_id)[:32],
            "ext_refs":   f"{{{self.name}}}{cluster_id}",
            "attributes": f"{self.config['name_id']}",
        }
