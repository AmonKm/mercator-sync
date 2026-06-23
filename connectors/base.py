from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """Classe commune pour toutes les sources de virtualisation."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    @abstractmethod
    def authenticate(self) -> None:
        """Récupère et stocke le token/session nécessaire"""
        ...

    @abstractmethod
    def fetch_clusters(self) -> list[dict]:
        """Retourne la liste brute des clusters."""
        ...

    @abstractmethod
    def fetch_vms(self, cluster_id: str) -> list[dict]:
        """Retourne la liste brute des VMs pour un cluster donnée."""
        ...

    @abstractmethod
    def enrich_vm(self, vm_id: str, vm: dict) -> dict:
        """
        Ajoute les détails guest (IP, OS...) au dict VM brut.
        Peut déclencher des appels supplémentaires (vCenter)
        ou ne rien faire si tout est déjà présent (XOA).
        """
        ...

    @abstractmethod
    def build_vm_payload(self, vm_id: str, enriched: dict) -> dict:
        """Construit le payload Mercator pour une VM."""
        ...

    @abstractmethod
    def build_cluster_payload(self, cluster_id: str, cluster: dict) -> dict:
        """Construit le payload Mercator pour un cluster."""
        ...
