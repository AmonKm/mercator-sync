import os
import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .base import BaseConnector
# FR : Classe Vcenter étant une sous-instance de la classe "BaseConnector" pour permettre de se baser sur ses méthodes.
# EN : Vcenter class, a subclass of BaseConnector, to inherit its methods.
class VCenterConnector(BaseConnector):

    def authenticate(self) -> None: 
        # FR : Méthode pour l'authentification. Crée un header avec le login/mdp et crée les variables selon l'instance. Ne renvoie rien.
        # EN : Authentication method. Builds a header with the login/password and sets the instance variables accordingly. Returns None.
        user   = os.environ[self.config["auth"]["username_env"]] 
        pwd    = os.environ[self.config["auth"]["password_env"]]
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
        # FR : Méthode qui permet d'aller chercher l'ensemble des clusters. Renvoie une liste de dictionnaires, la liste des clusters.
        # EN : Method that fetches all clusters. Returns a list of dictionaries (the list of clusters).    
        requête = requests.get(
            f"{self.base_url}/api/vcenter/cluster",
            headers=self.headers, verify=self.verify, timeout=10
        )
        requête.raise_for_status()
        return requête.json()

    def fetch_vms(self, cluster_id: str) -> list[dict]:
        # FR : Méthode qui prend en argument l'id d'un cluster pour parcourir les VMs de ce cluster. Renvoie une liste de dictionnaires (VMs).
        # EN : Method that takes a cluster id as argument to loop over its VMs. Returns a list of dictionaries (VMs).
        requête = requests.get(
            f"{self.base_url}/api/vcenter/vm",
            params={"clusters": cluster_id},
            headers=self.headers, verify=self.verify, timeout=10
        )
        requête.raise_for_status()
        return requête.json()

    def enrich_vm(self, vm_id: str, _vm: dict) -> dict:
        # FR : Méthode qui prend en argument l'id d'une VM et son dictionnaire de données et renvoie le dictionnaire associé avec les données de la VM, deux requêtes pour récupérer l'IP en plus.
        # EN : Method that takes a VM id and its data dictionary as arguments, and returns the dictionary enriched with the VM's data. Two extra requests are made to retrieve the IP.
        """Deux appels vCenter : détails VM + identité guest."""
        r_details = requests.get(
            f"{self.base_url}/api/vcenter/vm/{vm_id}",
            headers=self.headers, verify=self.verify, timeout=10
        )
        r_details.raise_for_status()
        details = r_details.json()
        time.sleep(0.3)

        r_guest = requests.get(
            f"{self.base_url}/api/vcenter/vm/{vm_id}/guest/identity",
            headers=self.headers, verify=self.verify, timeout=10
        )
        guest = r_guest.json() if r_guest.status_code == 200 else {}

        return {
            **details,
            "guest": {
                "ip_address": guest.get("ip_address", ""),
            },
        }
    
    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict: 
        # FR : Méthode qui prend en argument l'id d'une vm et le dictionnaire d'infos d'une VM. Renvoie un dictionnaire adapté à Mercator.
        # EN : Method that takes a VM id and its info dictionary as arguments. Returns a dictionary formatted for Mercator.
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
            "attributes":       f"{self.config['name_id']}", # Work in progress
            "ext_refs": f"{{{self.name}}}{vm_id}",
            "disk": int(round(disks_list[0].get("capacity", 0) / 1024**3, 1)) if disks_list else 0
        }
    
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        # FR : Méthode qui prend en argument l'id d'un cluster. Renvoie un dictionnaire adapté à Mercator.
        # EN : Method that takes a cluster id as argument. Returns a dictionary formatted for Mercator.
        return {
            "name":       cluster.get("name", ""),
            "ext_refs": f"{{{self.name}}}{cluster_id}",
            "attributes":       f"{self.config['name_id']}",
            "type": "VMware",
            "description": f"Cluster provenant de la source : {self.name}"
        }
