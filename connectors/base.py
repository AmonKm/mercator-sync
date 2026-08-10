from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """
    FR : Interface commune pour toutes les sources de virtualisation.
    EN : Common interface for all virtualization sources.
    """

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    @abstractmethod
    def authenticate(self) -> None:
        """
        FR : Récupère et stocke le token/session nécessaire aux appels.
        EN : Retrieves and stores the token/session required for API calls.
        """
        ...

    @abstractmethod
    def fetch_clusters(self) -> list[dict]:
        """
        FR : Retourne la liste brute des clusters.
        EN : Returns the raw list of clusters.
        """
        ...

    @abstractmethod
    def fetch_vms(self, cluster_id: str) -> list[dict]:
        """
        FR : Retourne la liste brute des VMs pour un cluster donné.
        EN : Returns the raw list of VMs for a given cluster.
        """
        ...

    @abstractmethod
    def enrich_vm(self, vm_id: str, vm: dict) -> dict:
        """
        FR : Ajoute les détails guest (IP, OS...) au dict VM brut.
             Peut déclencher des appels supplémentaires (vCenter)
             ou ne rien faire.
        EN : Adds guest details (IP, OS...) to the raw VM dict.
             May trigger additional calls (vCenter)
             or do nothing.
        """
        ...

    @abstractmethod
    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict:
        """
        FR : Construit le payload Mercator pour une VM.
        EN : Builds the Mercator payload for a VM.
        """
        ...

    @abstractmethod
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        """
        FR : Construit le payload Mercator pour un cluster.
        EN : Builds the Mercator payload for a cluster.
        """
        ...
