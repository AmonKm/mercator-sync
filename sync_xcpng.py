import getpass
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# --------------------------------------------------------------------------------------------------
# Fonctions :

def read_xcpng_id(attributs:str): # Fonction qui prend en argument un champ attribut de Mercator et lit l'entrée xcpng_id:[ID] si elle existe puis renvoie l'ID
    for attribut in attributs.split(" "):
        if attribut.startswith("xcpng_id:"):
            return attribut.split(":")[1]
    return None 

def construire_payload(detail:dict)->dict: # Mapping des champs Mercator -> XOA, à revoir ?
    cpu = detail.get("CPUs", {}).get("number") # Mappage du champ CPUs
    mem_go = round(detail.get("memory", {}).get("size", 0) / (1024**3), 1) # Mappage du champ memory
    os_info = detail.get("os_version") or {} # Mappage du champ de la version de l'OS
    os_name = os_info.get("name", "") # Mappage du champ du nom de l'OS
    distro = os_info.get("distro", "") # Mappage du champ qui précise la distribution de la vm
    tags = detail.get("tags", []) # Mappage du champ tags

    attributs = f"xcpng_id:{detail['uuid']}" # Mappage du champ attribut en y mettant l'id xcpng
    if distro:
        attributs += f" distro:{distro}" # distro devient un attribut
    for tag in tags:
        attributs += f" {tag}" # On ajoute l'ensemble des tags s'il y en a

    payload = { # On crée le payload avec l'ensemble des champs
        "name": detail["name_label"],
        "description": f"VM importée de XOA ({detail['uuid']})<br>{detail.get('name_description', '')}",
        "operating_system": os_name,
        "address_ip": detail.get("mainIpAddress"),
        "cpu": cpu,
        "memory": mem_go,
        "attributes": attributs
    }
    return payload

# --------------------------------------------------------------------------------------------------
# Connexion à Mercator
BASE_URL_MERCATOR = "https://mercator.exemple.com" # URL de base de Mercator
print("Login")
login = 'VOTRE LOGIN ADMIN' # Compte pour accéder à l'API
password = getpass.getpass('Mot de passe Mercator : ') # Demande le mdp du compte

vheaders = {
    'accept': 'application/json',
    'content-type': 'application/json',
    'cache-control': 'no-cache'
}

response = requests.post( #Permet de récupérer le token API
    f'{BASE_URL_MERCATOR}/api/login',
    headers=vheaders,
    json={'login': login, 'password': password}
)
print(response.status_code) # Test

if response.status_code != 200:
    print("Échec de l'authentification")
    exit(1)

vheaders['Authorization'] = "Bearer " + response.json()['access_token']

requete = requests.get(f"{BASE_URL_MERCATOR}/api/logical-servers", headers=vheaders) # Requête pour obtenir les serveurs logiques de Mercator
serveurs = requete.json() 

# Index par xcpng_id -> Permet ensuite de savoir si l'objet XOA existe oui ou non sur Mercator
index = {}
for serveur in serveurs: # Parcours les serveurs logiques de Mercator
    if read_xcpng_id(serveur['attributes']) != None : # Si le champ attribut contient xcpng_id avec un id on :
        index[read_xcpng_id(serveur['attributes'])] = serveur["id"] # On l'index avec l'ID du serveur logique (Pour savoir lequel pointer si on veut update)

# --------------------------------------------------------------------------------------------------
# XOA
print("Token")
BASE_URL_XOA = "https://xoa.exemple.com"
token = getpass.getpass("Token d'authentification de XOA : ") # Renseigner son Token

headers = {
    "Cookie": f"authenticationToken={token}"
}

response = requests.get(
    f"{BASE_URL_XOA}/rest/v0/vms?filter=$pool:[ID_DU_POOL]&fields=name_label,power_state,href", # Requête les vms en filtrant sur un POOL avec les champs souhaités, le href étant l'id - Possible de ne pas filtrer
    headers=headers, verify=False, timeout=10
)
vms = response.json()

# --------------------------------------------------------------------------------------------------
# Requête finale
print("Les VMs :")
for vm in vms: #Pour toutes les vms de la requête XOA :
    detail = requests.get(f"{BASE_URL_XOA}{vm['href']}", headers=headers, verify=False, timeout=10).json() # On récupère les infos de la vm qu'on parcourt, le href est l'id
    payload = construire_payload(detail) # On construit son payload (mapping avec les champs mercator)

    if detail["uuid"] in index : # Update, si le xcpng_id est dans l'index (donc que la vm existe déjà dans mercator)
        requests.patch(f"{BASE_URL_MERCATOR}/api/logical-servers/{index[detail['uuid']]}", json=payload, headers=vheaders) # On update la vm avec les champs
        print("update", detail["name_label"])

    else: # Création
        requests.post(f"{BASE_URL_MERCATOR}/api/logical-servers", json=payload, headers=vheaders, verify=False) # On crée la vm avec les champs
        print("create", detail["name_label"])
