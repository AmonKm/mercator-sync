import os
import requests
from .base import BaseConnector 


class XoaConnector(BaseConnector): # Cette classe hérite directement de BaseConnector 

    def authenticate(self) -> None: # Méthode pour l'authentification. Créer un cookie avec le token et créer les variables selon l'instance. Ne renvoie rien.
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

    def fetch_clusters(self) -> list[dict]: # Permet d'aller chercher un cluster souhaité. Renvoie une liste de dictionnaire.
        pool_id = self.config["pool_id"]

        requête = requests.get(
            f"{self.base_url}/rest/v0/pools/{pool_id}",
            cookies=self.cookies, verify=self.verify, timeout=10
        )

        requête.raise_for_status()
        pool = requête.json()

        pool["id"] = pool_id  # s'assurer que l'id est présent à revoir

        return [pool]

    def fetch_vms(self, cluster_id: str) -> list[dict]: # Prend en argument l'id d'un cluster pour parcourir les VMs de ce cluster. Renvoie une liste de dictionnaire.
       requête= requests.get(
            f"{self.base_url}/rest/v0/vms",
            params={"filter": f"$pool:{cluster_id}", "fields": "id,name_label,power_state"},
            cookies=self.cookies, verify=self.verify, timeout=10
        )
       requête.raise_for_status()
       return requête.json()

    def enrich_vm(self, vm_id: str, _vm: dict) -> dict: # Prend en argument l'id d'une VM et renvoie le dictionnaire associé avec les données de la VM.
        requête= requests.get(
            f"{self.base_url}/rest/v0/vms/{vm_id}",
            cookies=self.cookies, verify=self.verify, timeout=10
        )
        requête.raise_for_status()
        return requête.json()

    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict: # Prend en argument l'id d'une vm et le dictionnaire d'infos d'une VM. Renvoie un dictionnaire adapté à Mercator.
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
    
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict: # Prend en argument l'id d'un cluster + le dictionnaire d'infos d'un cluster. Renvoie un dictionnaire adapté à Mercator.
        return {
            "name":       cluster.get("name_label", cluster_id)[:32],
            "ext_refs":   f"{{{self.name}}}{cluster_id}",
            "attributes": f"{self.config['name_id']}",
            "type": "XCP-ng",
            "description": f"Cluster provenant de la source : {self.name}"
        }
