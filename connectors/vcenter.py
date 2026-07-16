import os
import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# verify_ssl: false dans sources.yaml → ce warning apparaît sans cette ligne.
# Pour supprimer proprement : pointer verify_ssl vers le .pem du vCenter. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from .base import BaseConnector

class VCenterConnector(BaseConnector):

    def authenticate(self) -> None:
        user   = os.environ[self.config["auth"]["username_env"]] # On prend le login du fichier env en passant par le fichier yaml
        pwd    = os.environ[self.config["auth"]["password_env"]] # On prend le password du fichier env en passant par le fichier yaml
        verify = self.config.get("verify_ssl", True)
        self.base_url = os.environ[self.config["base_url"]]

        requête = requests.post(
            f"{self.base_url}/api/session",
            auth=(user, pwd), verify=verify
        )
        requête.raise_for_status()

        self.headers = {"vmware-api-session-id": requête.json()}
        self.verify  = verify

    def fetch_clusters(self) -> list[dict]:
        requête = requests.get(
            f"{self.base_url}/api/vcenter/cluster",
            headers=self.headers, verify=self.verify
        )
        requête.raise_for_status()
        return requête.json()

    def fetch_vms(self, cluster_id: str) -> list[dict]: # On parcours l'ensemble des vms PAR cluster
        requête = requests.get(
            f"{self.base_url}/api/vcenter/vm",
            params={"clusters": cluster_id},
            headers=self.headers, verify=self.verify
        )
        requête.raise_for_status()
        return requête.json()

    def enrich_vm(self, vm_id: str, vm: dict) -> dict:
        """Deux appels vCenter : détails VM + identité guest."""
        r_details = requests.get(
            f"{self.base_url}/api/vcenter/vm/{vm_id}",
            headers=self.headers, verify=self.verify
        )
        r_details.raise_for_status()
        details = r_details.json()
        time.sleep(0.3)

        r_guest = requests.get(
            f"{self.base_url}/api/vcenter/vm/{vm_id}/guest/identity",
            headers=self.headers, verify=self.verify
        )
        guest = r_guest.json() if r_guest.status_code == 200 else {}

        return {
            **details,
            "guest": {
                "ip_address": guest.get("ip_address", ""),
            },
        }
    
    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict:
        cpu     = enriched.get("cpu", {}).get("count")
        mem_go  = round(enriched.get("memory", {}).get("size_MiB", 0) / 1024, 1)
        ip      = enriched.get("guest", {}).get("ip_address", "")
        disks_list = list(enriched.get("disks", {}).values())
        return {
            "name":             enriched.get("identity", {}).get("name", ""),
            "description":      f"VM importée du Vcenter suivant : {self.name} ({vm_id})<br>{enriched.get('name_description', '')}",
            "operating_system": enriched.get("guest_OS", ""),
            "address_ip":       ip,
            "cpu":              cpu or 0,
            "memory":           mem_go or 0,
            "attributes":       f"{self.config['name_id']}", # A modifier si l'on veut faire un ajout
            "ext_refs": f"{{{self.name}}}{vm_id}",
            "disk": round(disks_list[0].get("capacity", 0) / 1024**3, 1) if disks_list else 0 # A changer, selon les cas !
        }
    
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        return {
            "name":       cluster.get("name", ""),
            "ext_refs": f"{{{self.name}}}{cluster_id}",
            "attributes":       f"{self.config['name_id']}",
            "type": "VMware",
            "description": f"Cluster provenant de la source : {self.name}"
        }
