import os
import requests
from .base import BaseConnector


class ProxmoxConnector(BaseConnector):

    def authenticate(self) -> None:
        token_id  = os.environ[self.config["auth"]["user_env"]]
        token_secret = os.environ[self.config["auth"]["token_env"]]
        self.headers = {"Authorization": f"PVEAPIToken={token_id}={token_secret}"}
        self.verify  = self.config.get("verify_ssl", True)
        self.base_url = os.environ[self.config["base_url"]]
        
    def fetch_clusters(self) -> list[dict]:

        requête = requests.get(
            f"{self.base_url}/api2/json/nodes",
            headers=self.headers, verify=self.verify, timeout=10
        )
        requête.raise_for_status()

        return requête.json()["data"]

    def fetch_vms(self, cluster_id: str) -> list[dict]:
       requête= requests.get(
            f"{self.base_url}/api2/json/nodes/{cluster_id}/qemu",
            headers=self.headers, verify=self.verify, timeout=10
        )
       requête.raise_for_status()
       return requête.json()["data"]

    def enrich_vm(self, vm_id: str, vm: dict) -> dict:
        node = vm.get("node", "pve")
        requête= requests.get(
            f"{self.base_url}/api2/json/nodes/{node}/qemu/{vm_id}/config",
            headers=self.headers, verify=self.verify, timeout=10
        )
        requête.raise_for_status()
        data = requête.json()["data"]

        requête_ip = requests.get(
            f"{self.base_url}/api2/json/nodes/{node}/qemu/{vm_id}/agent/network-get-interfaces",
            headers=self.headers, verify=self.verify, timeout=10
        )

        ips = ""

        if requête_ip.status_code == 200:
            for interface in requête_ip.json().get("data", {}).get("result", []):
                for sous_interface in interface.get("ip-addresses", []) :
                    if sous_interface.get("ip-address-type") == "ipv4" and not sous_interface["ip-address"].startswith("127."):
                        ips += f"{sous_interface['ip-address']} " if ips else sous_interface["ip-address"]
        data["ips"] = ips

        requête_os = requests.get(
            f"{self.base_url}/api2/json/nodes/{node}/qemu/{vm_id}/agent/get-osinfo",
            headers=self.headers, verify=self.verify, timeout=10
        )

        os_name = ""
        if requête_os.status_code == 200:
            os_data = requête_os.json().get("data", {}).get("result", {})
            os_name = os_data.get("pretty-name", "") or os_data.get("name", "")

        data["os_name"] = os_name

        return data

    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict:
        cpu    = enriched.get("cores", 1) * enriched.get("sockets", 1)
        mem_go = round(int(enriched.get("memory", 0)) / 1024, 1)
        os_name = enriched.get("os_name", "")
        attributs = f"{self.name}"

        return {
            "name": enriched.get("name", "")[:32],
            "description":      f"VM importée de : {self.name} ({vm_id})",
            "operating_system": os_name,
            "address_ip":       enriched.get("ips", ""),
            "cpu":              cpu,
            "memory":           mem_go,
            "attributes":       attributs,
            "ext_refs": f"{{{self.name}}}{vm_id}",
        }
    
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        return {
            "name":       cluster_id[:32],
            "ext_refs":   f"{{{self.name}}}{cluster_id}",
            "attributes": f"{self.config['name_id']}",
            "type": "Proxmox",
            "description": f"Cluster provenant de la source : {self.name}"
        }
