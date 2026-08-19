"""
FR :
transform.py Transformation Grist vers Mercator
Regroupe le mapping des champs Grist et la construction du payload data-processings attendu par Mercator.
"""
"""
EN:
transform.py Grist -> Mercator transformation
Groups the Grist field mapping and the construction of the data-processings payload expected by Mercator.
"""
import datetime
 
LAWFULNESS_MAP = {
    "La personne concernée a consenti au traitement de ses données à caractère personnel pour une ou plusieurs finalités spécifiques": "lawfulness_consent",
    "Le traitement est nécessaire à l'exécution d'un contrat auquel la personne concernée est partie ou à l'exécution de mesures précontractuelles prises à la demande de celle-ci": "lawfulness_contract",
    "Le traitement est nécessaire au respect d'une obligation légale à laquelle le responsable du traitement est soumis": "lawfulness_legal_obligation",
    "Le traitement est nécessaire à la sauvegarde des intérêts vitaux de la personne concernée ou d'une autre personne physique": "lawfulness_vital_interest",
    "Le traitement est nécessaire à l'exécution d'une mission d'intérêt public ou relevant de l'exercice de l'autorité publique dont est investi le responsable du traitement": "lawfulness_public_interest",
    "Le traitement est nécessaire aux fins des intérêts légitimes poursuivis par le responsable du traitement ou par un tiers": "lawfulness_legitimate_interest",
}
 
DATA_COLLECT_MAP = {
    'Etat_civil_identite_donnees_d_identification_images': "Etat civil & identité",
    'Vie_personnelle': "Vie personelle",
    'Vie_professionnelle': "Vie professionnelle",
    'Informations_d_ordre_economique_et_financier': "Données économiques",
    'Donnees_de_connexion': "Données de connexion",
    'Donnees_Internet': "Données Internet",
    'Donnees_de_localisation': "Données de localisation",
    'Existe_t_il_une_zone_de_saisie_libre_': "Zone de saisie libre",
    'Origine_raciale_ou_ethnique': "Origine raciale/ethnique [Sensible]",
    'Opinions_politiques': "Opinions politiques [Sensible]",
    'Convictions_religieuses_ou_philosophiques': "Convictions religieuses [Sensible]",
    'Appartenance_syndicale': "Appartenance syndicale [Sensible]",
    'Donnees_genetiques': "Données génétiques [Sensible]",
    'Donnees_biometriques_aux_fins_d_identifier_une_personne_physique_de_maniere_unique': "Données biométriques [Sensible]",
    'Donnees_concernant_la_sante': "Données de santé [Sensible]",
    'Vie_ou_orientation_sexuelle': "Données sexuelle [Sensible]",
    'Condamnations_penales_ou_infractions': "Condamnations pénales [Sensible]",
    'Numero_d_identification_national_unique': "NIR/INSEE [Sensible]",
}
 
 
# FR : Filtre les valeurs "L" (résiduel du format Grist pour les listes)
# EN : Filters out "L" values (leftover from Grist's list format)
def clean_list(val: list) -> list:
    if isinstance(val, list):
        return [v for v in val if v != "L"]
    return []
 
 
def list_to_str(val: list) -> str:
    return ", ".join(clean_list(val))
 
 
def build_recipients(fields: dict) -> str:
    parts = []
    for i in ["1", "2", "3", "4"]:
        org = fields.get(f"Destinataire_{i}_Organisme", "")
        typ = fields.get(f"Destinataire_{i}_Type", "")
        if org:
            parts.append(f"{org} ({typ})")
    return "<p>" + ", ".join(parts) + "</p>" if parts else ""
 
 
def build_transfert(fields: dict) -> str:
    parts = []
    for i in ["1", "2", "3", "4"]:
        org = fields.get(f"Destinataire_{i}_Organisme_hors_UE_", "")
        pays = fields.get(f"Destinataire_{i}_Pays_hors_UE_", "")
        typ = fields.get(f"Destinataire_{i}_Type_de_garanties_hors_UE_", "")
        link = fields.get(f"Destinataire_{i}_Lien_vers_le_doc_hors_UE_", "")
        if org:
            parts.append(
                f"{org} hors UE <li><br> Pays hors UE : {pays} </br>"
                f"<br> Type de garanties hors UE: {typ} </br>"
                f"<br>Lien vers le doc hors UE: {link}</br></li>"
            )
    return "<p>" + ", ".join(parts) + "</p>" if parts else ""
 
 
def build_lawfulness(fields: dict) -> dict:
    base = fields.get("Base_de_liceite_du_traitement", [])  # a revoir
    result = {v: 0 for v in LAWFULNESS_MAP.values()}
    for item in base:
        if item in LAWFULNESS_MAP:
            result[LAWFULNESS_MAP[item]] = 1
    return result
 
 
def build_data_collect(fields: dict) -> str:
    items = [label for key, label in DATA_COLLECT_MAP.items() if fields.get(key)]
    if not items:
        return ""
    liste = "".join(f"<li>{label}</li>" for label in items)
    return f"<br><strong>Données collectées</strong><ul>{liste}</ul>"
 
 
def build_type_traitement(fields: dict) -> str:
    items = clean_list(fields.get("TYPE_DE_TRAITEMENT", []))
    if not items:
        return ""
    liste = "".join(f"<li>{item.replace(chr(10), ' ')}</li>" for item in items)
    return f"<br><strong>Types de traitement</strong><ul>{liste}</ul>"
 
 
# FR : Résout les applications liées via l'index {grist_record_id: mercator_id}
#      passé en argument (construit une seule fois par run, plus un appel API par fiche)
# EN : Resolves related applications via the {grist_record_id: mercator_id} index
#      passed as an argument (built once per run, not one API call per sheet)
def liste_app(fields: dict, app_index: dict) -> list:
    liste_possible_app = [
        'Application_1_concernee_par_le_traitement',
        'Application_2_concernee_par_le_traitement',
        'Application_3_concernee_par_le_traitement',
    ]
    applications = []
    for app in liste_possible_app:
        grist_id = fields.get(app)
        if grist_id and grist_id in app_index:
            applications.append(app_index[grist_id])
    return applications
 
 
# FR : Construit le payload Mercator (data-processings) pour une fiche Grist donnée
# EN : Builds the Mercator payload (data-processings) for a given Grist sheet
def payload_grist(record: dict, app_index: dict) -> dict:
    fields = record.get("fields", {})
    lawfulness = build_lawfulness(fields)
    ma_date = datetime.date.today().isoformat()
 
    return {
        "name": fields["NOM_TRAITEMENT"],
        "description": (
            f"grist_uuid:{fields['UUID']}<br>"
            f"{fields.get('Description_du_traitement') or ''}"
            f"{build_data_collect(fields)}<br>"
            f"{build_type_traitement(fields)}"
        ),
        "ext_refs": f"{{Grist}}{fields['UUID']}",
        "legal_basis": fields.get('Reference_juridique_du_traitement') or '',
        "purpose": fields.get("Finalite_principale"),
        "responsible": fields.get("Entite_Responsable_du_traitement"),
        "retention": f"{fields.get('NOMBRE_DE_MOIS', '')} mois",
        "categories": list_to_str(fields.get("Cibles")),
        "data_collection_obligation": list_to_str(fields.get("Canaux_de_collecte")),
        "data_source": list_to_str(fields.get("Origine_des_donnees")),
        "automated_decision_making": fields.get("Recours_au_profilage_"),
        "recipients": build_recipients(fields),
        "transfert": build_transfert(fields),
        "lawfulness_consent": lawfulness["lawfulness_consent"],
        "lawfulness_contract": lawfulness["lawfulness_contract"],
        "lawfulness_legal_obligation": lawfulness["lawfulness_legal_obligation"],
        "lawfulness_vital_interest": lawfulness["lawfulness_vital_interest"],
        "lawfulness_public_interest": lawfulness["lawfulness_public_interest"],
        "lawfulness_legitimate_interest": lawfulness["lawfulness_legitimate_interest"],
        "update_date": ma_date,
        "applications": liste_app(fields, app_index),
    }
