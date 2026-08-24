import os
import requests
from .base import BaseConnector

# FR : Classe Proxmox étant une sous-instance de la classe "BaseConnector" pour permettre de se baser sur ses méthodes.
# EN : Proxmox class, a subclass of BaseConnector, to inherit its methods.
# FR : ATTENTION : la récupération de l'IP et de l'OS repose sur le QEMU Guest Agent. Celui-ci doit être installé et activé sur la VM (et l'option "QEMU Guest Agent" cochée dans les options de la VM côté Proxmox), sinon ces requêtes échouent silencieusement et les champs "ips" / "os_name" restent vides.
# EN : WARNING : IP and OS retrieval relies on the QEMU Guest Agent. It must be installed and enabled on the VM (and the "QEMU Guest Agent" option checked in the VM's Proxmox settings), otherwise these requests fail silently and the "ips" / "os_name" fields remain empty.
class ProxmoxConnector(BaseConnector):

    def authenticate(self) -> None: 
        # FR : Méthode pour l'authentification. Crée un header avec le l'id / token API et crée les variables selon l'instance. Ne renvoie rien.
        # EN : Authentication method. Builds a header with the login/password and sets the instance variables accordingly. Returns None.
        token_id  = os.environ[self.config["auth"]["user_env"]]
        token_secret = os.environ[self.config["auth"]["token_env"]]
        self.headers = {"Authorization": f"PVEAPIToken={token_id}={token_secret}"}
        self.verify  = self.config.get("verify_ssl", True)
        self.base_url = os.environ[self.config["base_url"]]
        
    def fetch_clusters(self) -> list[dict]: 
        # FR : Méthode qui permet d'aller chercher l'ensemble des clusters. Renvoie une liste de dictionnaires, la liste des clusters.
        # EN : Method that fetches all clusters. Returns a list of dictionaries (the list of clusters).     

        requête = requests.get(
            f"{self.base_url}/api2/json/nodes",
            headers=self.headers, verify=self.verify, timeout=10
        )
        requête.raise_for_status()

        return requête.json()["data"]

    def fetch_vms(self, cluster_id: str) -> list[dict]: 
        # FR : Méthode qui prend en argument l'id d'un cluster pour parcourir les VMs de ce cluster. Renvoie une liste de dictionnaires (VMs).
        # EN : Method that takes a cluster id as argument to loop over its VMs. Returns a list of dictionaries (VMs).
        requête= requests.get(
             f"{self.base_url}/api2/json/nodes/{cluster_id}/qemu",
             headers=self.headers, verify=self.verify, timeout=10
         )
        requête.raise_for_status()
        return requête.json()["data"]

    def enrich_vm(self, vm_id: str, vm: dict) -> dict: 
        # FR : Méthode qui prend en argument l'id d'une VM et son dictionnaire de données et renvoie le dictionnaire associé avec les données de la VM, deux requêtes pour récupérer l'IP en plus.
        # EN : Method that takes a VM id and its data dictionary as arguments, and returns the dictionary enriched with the VM's data. Two extra requests are made to retrieve the IP.
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
        # FR : Cas spécifique : la structure de données oblige à parcourir par sous-interface, ici on met plusieurs IPs si disponibles et on crée une entrée dans le dico.
        # EN : Specific case : the data model requires looping over sub-interfaces; here we set several IPs if available and add an entry to the dictionar
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
        # FR : Méthode qui prend en argument l'id d'une vm et le dictionnaire d'infos d'une VM. Renvoie un dictionnaire adapté à Mercator.
        # EN : Method that takes a VM id and its info dictionary as arguments. Returns a dictionary formatted for Mercator.
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
    
    def build_cluster_payload(self, cluster_id: str, _cluster: dict) -> dict: 
        # FR : Méthode qui prend en argument l'id d'un cluster. Renvoie un dictionnaire adapté à Mercator.
        # EN : Method that takes a cluster id as argument. Returns a dictionary formatted for Mercator.
        return {
            "name":       cluster_id[:32],
            "ext_refs":   f"{{{self.name}}}{cluster_id}",
            "attributes": f"{self.config['name_id']}",
            "type": "Proxmox",
            "description": f"Cluster provenant de la source : {self.name}"
        }
