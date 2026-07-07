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

    def fetch_vms(self, cluster_id: str) -> list[dict]: # On parcours l'ensemble des vms PAR cluster, même logique que xoa
        requête = requests.get(
            f"{self.base_url}/api/vcenter/vm",
            params={"clusters": cluster_id},
            headers=self.headers, verify=self.verify
        )
        requête.raise_for_status()
        return requête.json()

    def enrich_vm(self, vm_id: str, vm: dict) -> dict:
        """Deux appels vCenter : détails VM + identité guest. Au besoin il est possible d'ajouter des appels pour enrichir les données..."""
        r_details = requests.get(
            f"{self.base_url}/api/vcenter/vm/{vm_id}",
            headers=self.headers, verify=self.verify
        )
        r_details.raise_for_status()
        details = r_details.json()
        # print(details)
        time.sleep(0.3)

        r_guest = requests.get(
            f"{self.base_url}/api/vcenter/vm/{vm_id}/guest/identity",
            headers=self.headers, verify=self.verify
        )
        # guest/identity peut être indisponible (VM éteinte)
        guest = r_guest.json() if r_guest.status_code == 200 else {}

        return {
            **details,
            "guest": {
                "ip_address": guest.get("ip_address", ""),
                "full_name":  guest.get("full_name", {}),
            },
        }
    
    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict:
        cpu     = enriched.get("cpu", {}).get("count")
        mem_go  = round(enriched.get("memory", {}).get("size_MiB", 0) / 1024, 1)
        ip      = enriched.get("guest", {}).get("ip_address", "")
        info    = enriched.get("guest", {}).get("full_name", {}).get("default_message", "")

        return {
            "name":             enriched.get("identity", {}).get("name", ""),
            "description":      f"VM importée du Vcenter suivant : {self.base_url} ({vm_id})<br>{enriched.get('name_description', '')}", # Peut être mettre autre chose que url
            "operating_system": info,
            "address_ip":       ip,
            "cpu":              cpu or 0,
            "memory":           mem_go or 0,
            "attributes":       f"{self.config['name_id']}", # A modifier si l'on veut faire un ajout
            "ext_refs": f"{{{self.name}}}{vm_id}", # utilisation de ext refs !
        }
    
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        return {
            "name":       cluster.get("name", ""),
            "ext_refs": f"{{{self.name}}}{cluster_id}", 
            "attributes":       f"{self.config['name_id']}",
        }
