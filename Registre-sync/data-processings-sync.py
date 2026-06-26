#!/usr/bin/python3
import getpass
import requests
import datetime
# De la meme manière faire un .env explicite pour ce doc et structurer le code 
# Etat de test !
BASE_URL = "mon_lien_mercator"

def extract_grist_uuid(description: str) -> str | None:
    if not description:
        return None
    for line in description.splitlines():
        # print(description.splitlines())
        if line.startswith("<p>grist_uuid:"):
            return line.split("grist_uuid:")[1].strip()
    return None

def trouver_id(entete):
        requête = requests.get(f"{BASE_URL}/api/data-processings", headers=entete)
        index = {}
        for traitement in requête.json():  # plus de ["data"]
            description = traitement.get("description", "") or ""
            # print(description)
            val = extract_grist_uuid(description)
            if val:
                index[val] = traitement["id"]
        return index

def clean_list(val):
    if isinstance(val, list):
        return ", ".join(base for base in val if base != "L")
    return val or ""

def build_recipients(fields):
    parts = []
    for num in ["1", "2", "3", "4"]:
        org = fields.get(f"Destinataire_{num}_Organisme", "")
        typ = fields.get(f"Destinataire_{num}_Type", "")
        if org:
            parts.append(f"{org} ({typ})")
    return ", ".join(parts)

def build_transfert(fields):
    parts = []
    for num in ["1", "2", "3", "4"]:
        org = fields.get(f"Destinataire_{num}_Organisme_hors_UE_", "")
        pays = fields.get(f"Destinataire_{num}_Pays_hors_UE_", "")
        typ = fields.get(f"Destinataire_{num}_Type_de_garanties_hors_UE_", "")
        link = fields.get(f"Destinataire_{num}_Lien_vers_le_doc_hors_UE_", "")
        if org:
            parts.append(f"{org} hors UE <li><br> Pays hors UE : {pays} </br><br> Type de garanties hors UE: {typ} </br><br>Lien vers le doc hors UE: {link}</br></li>")
    return ", ".join(parts)

print("Login")
login = 'login_mercator'
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
# -------------------------------------------------------------------------------

print("Tests :")
response = requests.get(f"{BASE_URL}/api/data-processings/", headers=vheaders)
GRIST_BASE_URL = "https://grist.numerique.gouv.fr"
GRIST_API_KEY = "TOKEN_API" # mettre un fichier env
GRIST_DOC_ID = "ID_DU_DOCUMENT" # .env
GRIST_TABLE_ID = "Registre_des_Fiches_de_Traitements"  # à ajuster

headers = {"Authorization": f"Bearer {GRIST_API_KEY}"}

url = f"{GRIST_BASE_URL}/api/docs/{GRIST_DOC_ID}/tables/{GRIST_TABLE_ID}/records"
response = requests.get(url, headers=headers)
response.raise_for_status()

LAWFULNESS_MAP = {
    "La personne concernée a consenti au traitement de ses données à caractère personnel pour une ou plusieurs finalités spécifiques": "lawfulness_consent",
    "Le traitement est nécessaire à l'exécution d'un contrat auquel la personne concernée est partie ou à l'exécution de mesures précontractuelles prises à la demande de celle-ci": "lawfulness_contract",
    "Le traitement est nécessaire au respect d'une obligation légale à laquelle le responsable du traitement est soumis": "lawfulness_legal_obligation",
    "Le traitement est nécessaire à la sauvegarde des intérêts vitaux de la personne concernée ou d'une autre personne physique": "lawfulness_vital_interest",
    "Le traitement est nécessaire à l'exécution d'une mission d'intérêt public ou relevant de l'exercice de l'autorité publique dont est investi le responsable du traitement": "lawfulness_public_interest",
    "Le traitement est nécessaire aux fins des intérêts légitimes poursuivis par le responsable du traitement ou par un tiers": "lawfulness_legitimate_interest",
}

def build_lawfulness(fields):
    base = fields.get("Base_de_liceite_du_traitement", []) # a revoir
    result = {v: 0 for v in LAWFULNESS_MAP.values()}
    for item in base:
        # print(f"Mon item : {item}")
        # print(f"Ma base : {base}")
        if item in LAWFULNESS_MAP:
            result[LAWFULNESS_MAP[item]] = 1
    return result

def payload_grist(data):
        data_fields = data.get("fields", {})
        mon_dico = build_lawfulness(data_fields)
        return {
            "name": data["fields"]["NOM_TRAITEMENT"],
            "description": "grist_uuid:" + data["fields"]["UUID"] + "\n" + (data_fields.get("Description_du_traitement") or ""), # Ajouter type de traitement
            # "legal_basis": 
            "purpose":          data_fields.get("Finalite_principale"),
            "responsible":      data_fields.get("Entite_Responsable_du_traitement"),
            "legal_basis":      data_fields.get("Reference_juridique_du_traitement"),
            "retention": str(data_fields.get("NOMBRE_DE_MOIS", "")) + " mois",
            "categories":       clean_list(data_fields.get("Cibles")), 
            "data_collection_obligation":       clean_list(data_fields.get("Canaux_de_collecte")),
            "data_source":       clean_list(data_fields.get("Origine_des_donnees")),
            "automated_decision_making":        data_fields.get("Recours_au_profilage_"),
            "recipients":       build_recipients(data_fields),
            "transfert":        build_transfert(data_fields),
            "lawfulness_consent": mon_dico["lawfulness_consent"],
            "lawfulness_contract": mon_dico["lawfulness_contract"],
            "lawfulness_legal_obligation": mon_dico["lawfulness_legal_obligation"],
            "lawfulness_vital_interest": mon_dico["lawfulness_vital_interest"],
            "lawfulness_public_interest": mon_dico["lawfulness_public_interest"],
            "lawfulness_legitimate_interest": mon_dico["lawfulness_legitimate_interest"],
            "update_date": f"{datetime.datetime.now().year}-{datetime.datetime.now().month}-{datetime.datetime.now().day}"
        }
# TODO Généraliser le data get
mon_index = trouver_id(vheaders)

for record in response.json()["records"]:
    ok = record.get("fields", {}).get("STATUT") == '✅ Fiche traitée'
    uuid = record.get("fields", {}).get("UUID")
    # print(f"Mon INDEX DE FOUUFOUFOUFOUFOUOFU {mon_index}")
    if uuid in mon_index and ok :
            requête = requests.patch(
                f"{BASE_URL}/api/data-processings/{mon_index[uuid]}",
                json=payload_grist(record), headers=vheaders         )
            print(record)
    elif ok :
        requête = requests.post(
            f"{BASE_URL}/api/data-processings",
            json=payload_grist(record), headers=vheaders
        )
        print(requête.text)


# TODO : 
# Verifier le statut et si validé importé sinon rien
# Mapper le reste des champs
# Structurer ça en objets ! Créer une classe Grist etc... et un mercator client ! Répartir en 3 files



# name : fields, NOM_TRAITEMENT
# description : fields, Description_du_traitement
# purpose : fields, Finalite_principale
# responsible : fields, Entite_Responsable_du_traitement
# legal_basis : fields, Reference_juridique_du_traitement
# retention : fields, NOMBRE_DE_MOIS
# categories -> Html, prendre la liste et formalisé ça en balise liste parcourir le champ fields, Cibles
# data_collection_obligation ->  Champ texte -> Pareil parcours la liste et genere un str avec l'ensemble
# data_source -> texte str pareil parcours la liste et genere un str
# automated_decision_making -> Texte str lambda la c booléen ....
# recipients -> Catégorie de dest en html à convertir ! Complexe, doit parcourir le dico et prendre tout de Destinataire_ ...
# transfert -> idem html donc convert et j'imagine tt les dest hors ue ? 
# lawfulness - truc à cocher dans la base juridique de traitement il y en a 6, valeur 0 = non, 1 = oui à verif
