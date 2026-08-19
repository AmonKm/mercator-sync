"""
FR :
grist_client.py Client Grist
Regroupe l'authentification et les appels à l'API Grist (lecture des fiches
de traitement, gestion de la table de mappage des applications).
"""
"""
EN:
grist_client.py Grist Client
Groups authentication and calls to the Grist API (reading processing
sheets, managing the application mapping table).
"""
import os
import requests
 
class GristClient:
    # FR : Classe permettant de gérer une session Grist et d'exposer les méthodes associées
    # EN : Class that manages a Grist session and exposes the related methods
    def __init__(self, config: dict):
        base = config["destination"]["grist"]
        # FR : Prend l'entrée grist avec les différentes sous-entrées dans sources.yaml
        # EN : Get the grist entry and its sub-entries from sources.yaml
 
        self.base_url = base["base_url"]
        # FR : URL Grist, dans sources.yaml
        # EN : Grist URL, in sources.yaml
 
        self.doc_id = os.environ[base["auth"]["doc_id_env"]]
        # FR : ID du document Grist, défini dans .env et référencé dans sources.yaml
        # EN : Grist document ID, defined in .env and referenced in sources.yaml
 
        api_token = os.environ[base["auth"]["token_env"]]
        # FR : Token API Grist, défini dans .env et référencé dans sources.yaml
        # EN : Grist API token, defined in .env and referenced in sources.yaml
 
        self.table_id = base["table_id"]
        # FR : Table des fiches de traitement
        # EN : Processing sheets table
 
        self.mapping_table_id = base["mapping_table_id"]
        # FR : Table de mappage application <-> id Mercator
        # EN : Application <-> Mercator id mapping table
 
        self.headers = {"Authorization": f"Bearer {api_token}"}
 
    # FR : Récupère tous les records d'une table (fiches de traitement par défaut)
    # EN : Fetches all records from a table (processing sheets by default)
    def get_records(self, table_id: str = None) -> list[dict]:
        table = table_id or self.table_id
        requête = requests.get(
            f"{self.base_url}/api/docs/{self.doc_id}/tables/{table}/records",
            headers=self.headers,
        )
        requête.raise_for_status()
        return requête.json()["records"]
 
    # FR : Supprime une liste de records par leurs ids dans une table donnée
    # EN : Deletes a list of records by their ids in a given table
    def delete_records(self, table_id: str, ids: list[int]) -> None:
        if not ids:
            return
        requête = requests.post(
            f"{self.base_url}/api/docs/{self.doc_id}/tables/{table_id}/data/delete",
            json=ids,
            headers=self.headers,
        )
        requête.raise_for_status()
 
    # FR : Crée une liste de records dans une table donnée
    # EN : Creates a list of records in a given table
    def post_records(self, table_id: str, records: list[dict]) -> dict:
        if not records:
            return {}
        requête = requests.post(
            f"{self.base_url}/api/docs/{self.doc_id}/tables/{table_id}/records",
            json={"records": records},
            headers=self.headers,
        )
        requête.raise_for_status()
        return requête.json()
 
    # FR : Met à jour une liste de records existants (par leur id Grist) dans une table donnée
    # EN : Updates a list of existing records (by their Grist id) in a given table
    def patch_records(self, table_id: str, records: list[dict]) -> None:
        if not records:
            return
        requête = requests.patch(
            f"{self.base_url}/api/docs/{self.doc_id}/tables/{table_id}/records",
            json={"records": records},
            headers=self.headers,
        )
        requête.raise_for_status()
 
    # FR : Met à jour la table de mappage application <-> id Mercator sans jamais
    #      supprimer/recréer les lignes existantes : les colonnes "Application_X"
    #      des fiches de traitement sont des références Grist vers l'id de ligne
    #      de cette table. Un delete+repopulate change ces ids et casse tous les
    #      liens déjà établis dans les fiches, même si le contenu est identique.
    #      On ne supprime donc que les lignes dont l'appli Mercator a disparu.
    # EN : Updates the application <-> Mercator id mapping table without ever
    #      deleting/recreating existing rows: the "Application_X" columns on
    #      the processing sheets are Grist references to this table's row id.
    #      A delete+repopulate changes those ids and breaks every link already
    #      set on the sheets, even when the content is identical. We therefore
    #      only delete rows whose Mercator application no longer exists.
    def sync_applications_mercator(self, mercator) -> None:
        existants = self.get_records(self.mapping_table_id)
        index = {record["fields"]["mercator_id"]: record["id"] for record in existants}
 
        apps = mercator.get("/api/applications")
        seen_mercator_ids = set()
        a_creer = []
        a_maj = []
        for app in apps:
            seen_mercator_ids.add(app["id"])
            if app["id"] in index:
                a_maj.append({"id": index[app["id"]], "fields": {"name": app["name"]}})
            else:
                a_creer.append({"fields": {"mercator_id": app["id"], "name": app["name"]}})
 
        self.patch_records(self.mapping_table_id, a_maj)
        self.post_records(self.mapping_table_id, a_creer)
 
        # FR : Applis Mercator disparues -> la ligne de mappage ne sert plus à rien
        # EN : Mercator applications that disappeared -> the mapping row is now useless
        orphelins = [
            grist_id for mercator_id, grist_id in index.items()
            if mercator_id not in seen_mercator_ids
        ]
        self.delete_records(self.mapping_table_id, orphelins)
 
    # FR : Construit l'index {grist_record_id: mercator_id} depuis la table de mappage
    # EN : Builds the {grist_record_id: mercator_id} index from the mapping table
    def get_app_index(self) -> dict:
        records = self.get_records(self.mapping_table_id)
        return {record["id"]: record["fields"]["mercator_id"] for record in records}
