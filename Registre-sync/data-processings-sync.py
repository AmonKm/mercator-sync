#!/usr/bin/python3
# TODO Préciser le type des variables
#-----------------------------------------------------------------------------
# Import
#-----------------------------------------------------------------------------
import requests
import getpass
import datetime
import re
#-----------------------------------------------------------------------------
# Import
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Authentification Mercator
#-----------------------------------------------------------------------------
BASE_URL = "https://mercator.exemple.fr"
print("Login")
login = 'Mon compte admin'
password = getpass.getpass('Mot de passe : ')

vheaders = {
    'accept': 'application/json',
    'content-type': 'application/json',
    'cache-control': 'no-cache'
}

response = requests.post(
    f'{BASE_URL}/api/login',
    headers=vheaders,
    json={'login': login, 'password': password}
)
print(response.status_code)

if response.status_code != 200:
    print("Échec de l'authentification")
    exit(1)

vheaders['Authorization'] = "Bearer " + response.json()['access_token']
#-----------------------------------------------------------------------------
# Authentification Mercator
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Authentification Grist
#-----------------------------------------------------------------------------
GRIST_BASE_URL = "https://grist.numerique.gouv.fr"
GRIST_API_KEY = "TOKEN" 
GRIST_DOC_ID = "ID du document"
GRIST_TABLE_ID = "Registre_des_Fiches_de_Traitements"  

headers = {"Authorization": f"Bearer {GRIST_API_KEY}"}

url = f"{GRIST_BASE_URL}/api/docs/{GRIST_DOC_ID}/tables/{GRIST_TABLE_ID}/records"
response = requests.get(url, headers=headers)
response.raise_for_status()
#-----------------------------------------------------------------------------
# Authentification Grist
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Remplissage de la table app vers Grist
#-----------------------------------------------------------------------------
def sync_applications_mercator():
    requête = requests.get(f"{BASE_URL}/api/applications", headers=vheaders)
    apps = requête.json()
    print(apps)
    records = [
        {"fields": {"mercator_id": app["id"], "name": app["name"]}}
        for app in apps
    ]
    
    requete2 = requests.post(
        f"{GRIST_BASE_URL}/api/docs/{GRIST_DOC_ID}/tables/Mercator_mappage/records",
        json={"records": records},
        headers=headers
    )
    requete = requests.get(
    f"{GRIST_BASE_URL}/api/docs/{GRIST_DOC_ID}/tables",
    headers=headers
    )
    print(r.json())

    print(requete2.status_code, requete2.text)
sync_applications_mercator()
#-----------------------------------------------------------------------------
# Remplissage de la table app vers Grist
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Variables pour Grist
#-----------------------------------------------------------------------------
LAWFULNESS_MAP = {
    "La personne concernée a consenti au traitement de ses données à caractère personnel pour une ou plusieurs finalités spécifiques": "lawfulness_consent",
    "Le traitement est nécessaire à l'exécution d'un contrat auquel la personne concernée est partie ou à l'exécution de mesures précontractuelles prises à la demande de celle-ci": "lawfulness_contract",
    "Le traitement est nécessaire au respect d'une obligation légale à laquelle le responsable du traitement est soumis": "lawfulness_legal_obligation",
    "Le traitement est nécessaire à la sauvegarde des intérêts vitaux de la personne concernée ou d'une autre personne physique": "lawfulness_vital_interest",
    "Le traitement est nécessaire à l'exécution d'une mission d'intérêt public ou relevant de l'exercice de l'autorité publique dont est investi le responsable du traitement": "lawfulness_public_interest",
    "Le traitement est nécessaire aux fins des intérêts légitimes poursuivis par le responsable du traitement ou par un tiers": "lawfulness_legitimate_interest",
}

UUID_RE = re.compile(r"grist_uuid:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")

data_collect_map = {
    'Etat_civil_identite_donnees_d_identification_images': "Etat civil & identité", 
    'Vie_personnelle' : "Vie personelle", 
    'Vie_professionnelle' : "Vie professionnelle", 
    'Informations_d_ordre_economique_et_financier': "Données économiques", 
    'Donnees_de_connexion': "Données de connexion", 
    'Donnees_Internet':"Données Internet", 
    'Donnees_de_localisation':"Données de localisation", 
    'Existe_t_il_une_zone_de_saisie_libre_':"Zone de saisie libre", 
    'Origine_raciale_ou_ethnique': "Origine raciale/ethnique [Sensible]", 
    'Opinions_politiques': "Opinions politiques [Sensible]", 
    'Convictions_religieuses_ou_philosophiques': "Convictions religieuses [Sensible]",
    'Appartenance_syndicale': "Appartenance syndicale [Sensible]", 
    'Donnees_genetiques' : "Données génétiques [Sensible]", 
    'Donnees_biometriques_aux_fins_d_identifier_une_personne_physique_de_maniere_unique' : "Données biométriques [Sensible]", 
    'Donnees_concernant_la_sante':"Données de santé [Sensible]", 
    'Vie_ou_orientation_sexuelle': "Données sexuelle [Sensible]", 
    'Condamnations_penales_ou_infractions': "Condamnations pénales [Sensible]", 
    'Numero_d_identification_national_unique': "NIR/INSEE [Sensible]", 
    }

ma_date = f"{datetime.datetime.now().year}-{datetime.datetime.now().month}-{datetime.datetime.now().day}"
#-----------------------------------------------------------------------------
# Variables pour Grist
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Fonctions
#-----------------------------------------------------------------------------

def extract_grist_uuid(description: str) -> str | None:
    if not description:
        return None
    match = UUID_RE.search(description)
    return match.group(1) if match else None

def trouver_id(entete):
        requête = requests.get(f"{BASE_URL}/api/data-processings", headers=entete)
        index = {}
        for traitement in requête.json():  # plus de ["data"]
            description = traitement.get("description", "") or ""
            val = extract_grist_uuid(description)
            if val:
                index[val] = traitement["id"]
        return index
mon_index = trouver_id(vheaders)

def clean_list(val):
    if isinstance(val, list):
        return [v for v in val if v != "L"]
    return []

def list_to_str(val):
    return ", ".join(clean_list(val))

def build_recipients(fields):
    parts = []
    for i in ["1", "2", "3", "4"]:
        org = fields.get(f"Destinataire_{i}_Organisme", "")
        typ = fields.get(f"Destinataire_{i}_Type", "")
        if org:
            parts.append(f"{org} ({typ})")
    return "<p>" + ", ".join(parts) + "</p>" if parts else ""

def build_transfert(fields):
    parts = []
    for i in ["1", "2", "3", "4"]:
        org = fields.get(f"Destinataire_{i}_Organisme_hors_UE_", "")
        pays = fields.get(f"Destinataire_{i}_Pays_hors_UE_", "")
        typ = fields.get(f"Destinataire_{i}_Type_de_garanties_hors_UE_", "")
        link = fields.get(f"Destinataire_{i}_Lien_vers_le_doc_hors_UE_", "")
        if org:
            parts.append(f"{org} hors UE <li><br> Pays hors UE : {pays} </br><br> Type de garanties hors UE: {typ} </br><br>Lien vers le doc hors UE: {link}</br></li>")
    return "<p>" + ", ".join(parts) + "</p>" if parts else ""

def build_lawfulness(fields):
    base = fields.get("Base_de_liceite_du_traitement", []) # a revoir
    result = {v: 0 for v in LAWFULNESS_MAP.values()}
    for item in base:
        if item in LAWFULNESS_MAP:
            result[LAWFULNESS_MAP[item]] = 1
    return result

def build_data_collect(fields):
    items = [
        label for key, label in data_collect_map.items()
        if fields.get(key)
    ]
    if not items:
        return ""
    liste = "".join(f"<li>{label}</li>" for label in items)
    return f"<br><strong>Données collectées</strong><ul>{liste}</ul>"
               
def build_type_traitement(fields):
    items = clean_list(fields.get("TYPE_DE_TRAITEMENT", []))
    if not items:
        return ""
    liste = "".join(f"<li>{item.replace(chr(10), ' ')}</li>" for item in items)
    return f"<br><strong>Types de traitement</strong><ul>{liste}</ul>"

def get_grist_app_index():
    r = requests.get(
        f"{GRIST_BASE_URL}/api/docs/{GRIST_DOC_ID}/tables/Mercator_mappage/records",
        headers=headers
    )
    index = {}
    for record in r.json()["records"]:
        index[record["id"]] = record["fields"]["mercator_id"]
    return index

def liste_app(fields):
    grist_app_index = get_grist_app_index()
    liste_possible_app = [
        'Application_1_concernee_par_le_traitement',
        'Application_2_concernee_par_le_traitement',
        'Application_3_concernee_par_le_traitement'
    ]
    applications = []
    for app in liste_possible_app:
        grist_id = fields.get(app)
        if grist_id and grist_id in grist_app_index:
            applications.append(grist_app_index[grist_id])
    return applications

def payload_grist(data):
        data_fields = data.get("fields", {})
        mon_dico = build_lawfulness(data_fields)
        return {
            "name": data["fields"]["NOM_TRAITEMENT"],
            "description": f"grist_uuid:{data['fields']['UUID']}<br>{data_fields.get('Description_du_traitement') or ''}{build_data_collect(data_fields)}<br>{build_type_traitement(data_fields)}",            
            "legal_basis": (data_fields.get('Reference_juridique_du_traitement') or ''),
            "purpose":          data_fields.get("Finalite_principale"),
            "responsible":      data_fields.get("Entite_Responsable_du_traitement"),
            "retention": str(data_fields.get("NOMBRE_DE_MOIS", "")) + " mois",
            "categories":       list_to_str(data_fields.get("Cibles")), 
            "data_collection_obligation":       list_to_str(data_fields.get("Canaux_de_collecte")),
            "data_source":       list_to_str(data_fields.get("Origine_des_donnees")),
            "automated_decision_making":        data_fields.get("Recours_au_profilage_"),
            "recipients":       build_recipients(data_fields),
            "transfert":        build_transfert(data_fields),
            "lawfulness_consent": mon_dico["lawfulness_consent"],
            "lawfulness_contract": mon_dico["lawfulness_contract"],
            "lawfulness_legal_obligation": mon_dico["lawfulness_legal_obligation"],
            "lawfulness_vital_interest": mon_dico["lawfulness_vital_interest"],
            "lawfulness_public_interest": mon_dico["lawfulness_public_interest"],
            "lawfulness_legitimate_interest": mon_dico["lawfulness_legitimate_interest"],
            "update_date": ma_date,
            "applications": liste_app(data_fields),
        }
#-----------------------------------------------------------------------------
# Fonctions
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Appel principal
#-----------------------------------------------------------------------------

for record in response.json()["records"]:
    ok = record.get("fields", {}).get("STATUT") == '✅ Fiche traitée'
    uuid = record.get("fields", {}).get("UUID")
    if uuid in mon_index and ok :
            requete = requests.patch(
                f"{BASE_URL}/api/data-processings/{mon_index[uuid]}",
                json=payload_grist(record), headers=vheaders         )
    elif ok :
        requete = requests.post(
            f"{BASE_URL}/api/data-processings",
            json=payload_grist(record), headers=vheaders
        )
#-----------------------------------------------------------------------------
# Appel principal
#-----------------------------------------------------------------------------

# TODO : 
# Structurer ça en objets ! Créer une classe Grist etc... et un mercator client ! Répartir en 3 files et env
