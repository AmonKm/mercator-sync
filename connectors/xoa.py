import os
import requests
from .base import BaseConnector 

# FR : Classe XOA étant une sous-instance de la classe "BaseConnector" pour permettre de se baser sur ses méthodes.
# EN : XOA class, a subclass of BaseConnector, to inherit its methods.
class XoaConnector(BaseConnector):

    def authenticate(self) -> None: 
        # FR : Méthode pour l'authentification. Crée un token valable une heure avec le login/mdp et crée les variables selon l'instance. Ne renvoie rien.
        # EN : Authentication method. Generates a token valid for one hour using the login/password, and sets the instance variables accordingly. Returns None.
        # token = os.environ[self.config["auth"]["token_env"]]
        # self.cookies = {"authenticationToken": token}
        # self.verify  = self.config.get("verify_ssl", True)
        self.base_url = os.environ[self.config["base_url"]]
        user  = os.environ[self.config["auth"]["username_env"]]
        pwd   = os.environ[self.config["auth"]["password_env"]]
        self.verify = self.config.get("verify_ssl", True)
        
        requête = requests.post(
            f"{self.base_url}/rest/v0/users/me/authentication_tokens",
            auth=(user, pwd), verify=self.verify,
            json={"description": "token mercator-sync auto", "expiresIn": "1 hour" }
        )
        requête.raise_for_status()
        token = requête.json()["token"]["id"]
        self.cookies = {"authenticationToken": token}

    def fetch_clusters(self) -> list[dict]:
        # FR : Méthode qui permet d'aller chercher l'ensemble des clusters. Renvoie une liste de dictionnaires, la liste des clusters.
        # EN : Method that fetches all clusters. Returns a list of dictionaries (the list of clusters).    
        pool_id = self.config["pool_id"]

        requête = requests.get(
            f"{self.base_url}/rest/v0/pools/{pool_id}",
            cookies=self.cookies, verify=self.verify, timeout=10
        )

        requête.raise_for_status()
        pool = requête.json()

        pool["id"] = pool_id

        return [pool]

    def fetch_vms(self, cluster_id: str) -> list[dict]:
        # FR : Méthode qui prend en argument l'id d'un cluster pour parcourir les VMs de ce cluster. Renvoie une liste de dictionnaires (VMs).
        # EN : Method that takes a cluster id as argument to loop over its VMs. Returns a list of dictionaries (VMs).
       requête= requests.get(
            f"{self.base_url}/rest/v0/vms",
            params={"filter": f"$pool:{cluster_id}", "fields": "id,name_label,power_state"},
            cookies=self.cookies, verify=self.verify, timeout=10
        )
       requête.raise_for_status()
       return requête.json()

    def enrich_vm(self, vm_id: str, _vm: dict) -> dict:
        # FR : Méthode qui prend en argument l'id d'une VM et son dictionnaire de données et renvoie le dictionnaire associé avec les données de la VM, deux requêtes pour récupérer d'autres informations.
        # EN : Method that takes a VM id and its data dictionary as arguments, and returns the dictionary enriched with the VM's data. Two extra requests are made to retrieve other informations.
        requête= requests.get(
            f"{self.base_url}/rest/v0/vms/{vm_id}",
            cookies=self.cookies, verify=self.verify, timeout=10
        )
        requête.raise_for_status()
        return requête.json()

    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict:
        # FR : Méthode qui prend en argument l'id d'une vm et le dictionnaire d'infos d'une VM. Renvoie un dictionnaire adapté à Mercator.
        # EN : Method that takes a VM id and its info dictionary as arguments. Returns a dictionary formatted for Mercator.
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
            "ext_refs": f"{{{self.name}}}{vm_id}",
        }
    
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        # FR : Méthode qui prend en argument l'id d'un cluster. Renvoie un dictionnaire adapté à Mercator.
        # EN : Method that takes a cluster id as argument. Returns a dictionary formatted for Mercator.
        return {
            "name":       cluster.get("name_label", cluster_id)[:32],
            "ext_refs":   f"{{{self.name}}}{cluster_id}",
            "attributes": f"{self.config['name_id']}",
            "type": "XCP-ng",
            "description": f"Cluster provenant de la source : {self.name}"
        }
