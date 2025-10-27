from flask import Flask, request, jsonify
import os
import requests
import json
import logging
from datetime import datetime
import base64
import threading
import time
from urllib.parse import urlparse

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Hook de démarrage pour Gunicorn
@app.before_first_request
def startup():
    """Démarrage automatique du monitoring"""
    logger.info("Démarrage automatique du monitoring...")
    start_monitoring()

# Configuration Jira depuis les variables d'environnement
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')
JIRA_ISSUE_TYPE = os.getenv('JIRA_ISSUE_TYPE', 'Task')

# Configuration du monitoring
MONITORED_APIS_RAW = os.getenv('MONITORED_APIS', '')  # Format: URL|NOM_API,URL|NOM_API
HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))  # secondes
TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', '10'))  # secondes
RETRY_ATTEMPTS = int(os.getenv('HEALTH_CHECK_RETRY', '3'))

# Configuration des tickets
TICKET_SUMMARY_PREFIX = os.getenv('TICKET_SUMMARY_PREFIX', '[CRITICAL] API DOWN')
TICKET_DESCRIPTION_MESSAGE = os.getenv('TICKET_DESCRIPTION_MESSAGE', "L'API ne répond plus aux health checks")

# Parser les APIs monitorées
def parse_monitored_apis():
    """
    Parse les APIs monitorées depuis la variable d'environnement
    Format: URL|NOM_API,URL|NOM_API
    """
    apis = []
    if MONITORED_APIS_RAW:
        for api_config in MONITORED_APIS_RAW.split(','):
            api_config = api_config.strip()
            if '|' in api_config:
                url, name = api_config.split('|', 1)
                apis.append({'url': url.strip(), 'name': name.strip()})
            else:
                # Format legacy: juste l'URL
                apis.append({'url': api_config, 'name': urlparse(api_config).netloc})
    return apis

MONITORED_APIS = parse_monitored_apis()

# État du monitoring
api_status = {}  # {url: {'status': 'up'/'down', 'last_check': datetime, 'consecutive_failures': int, 'name': str}}
monitoring_thread = None

# Headers pour l'authentification Jira
def get_jira_headers():
    # Utiliser l'authentification Basic avec username:password
    credentials = f"{JIRA_USERNAME}:{JIRA_API_TOKEN}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }

def check_api_health(api_url):
    """
    Vérifie la santé d'une API en effectuant un health check
    """
    try:
        # Nettoyer l'URL
        clean_url = api_url.strip()
        if not clean_url:
            return False, "URL vide"
        
        # Ajouter /actuator/health si ce n'est pas déjà présent
        if not clean_url.endswith('/actuator/health'):
            clean_url = clean_url.rstrip('/') + '/actuator/health'
        
        # Effectuer la requête avec timeout
        response = requests.get(clean_url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                # Vérifier le statut dans la réponse JSON
                if health_data.get('status') == 'UP':
                    return True, "API UP"
                else:
                    return False, f"API DOWN - Status: {health_data.get('status')}"
            except json.JSONDecodeError:
                # Si ce n'est pas du JSON, considérer que c'est OK si 200
                return True, "API UP (non-JSON response)"
        else:
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection Error"
    except Exception as e:
        return False, f"Error: {str(e)}"

def create_jira_ticket(ticket_type, **kwargs):
    """
    Crée un ticket Jira pour les APIs down
    
    Args:
        ticket_type: 'api_down'
        **kwargs: Données spécifiques (api_url, api_name, error_message)
    """
    try:
        if ticket_type == 'api_down':
            # Ticket pour API down
            api_url = kwargs['api_url']
            api_name = kwargs['api_name']
            error_message = kwargs['error_message']
            
            fields = {
                "project": {"key": JIRA_PROJECT_KEY},
                "summary": f"{TICKET_SUMMARY_PREFIX} - {api_name}",
                "description": f"{TICKET_DESCRIPTION_MESSAGE}",
                "issuetype": {"name": JIRA_ISSUE_TYPE}
            }
                
        else:
            raise ValueError(f"Type de ticket non supporté: {ticket_type}. Seul 'api_down' est supporté.")
        
        # Envoi de la requête à Jira
        jira_ticket = {"fields": fields}
        response = requests.post(
            f"{JIRA_URL}/rest/api/2/issue",
            headers=get_jira_headers(),
            json=jira_ticket
        )
        
        if response.status_code == 201:
            ticket_data = response.json()
            logger.info(f"Ticket Jira créé ({ticket_type}): {ticket_data['key']}")
            return {
                "success": True,
                "ticket_key": ticket_data['key'],
                "ticket_url": f"{JIRA_URL}/browse/{ticket_data['key']}"
            }
        else:
            logger.error(f"Erreur création ticket Jira: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"Erreur Jira: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Erreur création ticket: {str(e)}")
        return {"success": False, "error": str(e)}

# Support Prometheus supprimé pour le moment

def monitoring_worker():
    """
    Thread de monitoring qui vérifie périodiquement la santé des APIs
    """
    global api_status
    
    logger.info("Thread de monitoring démarré")
    
    while True:
        try:
            logger.debug(f"Début du cycle de monitoring pour {len(MONITORED_APIS)} API(s)")
            for api in MONITORED_APIS:
                api_url = api['url']
                api_name = api['name']
                
                if not api_url.strip():
                    continue
                    
                clean_url = api_url.strip()
                is_healthy, message = check_api_health(clean_url)
                current_time = datetime.now()
                
                # Initialiser le statut si c'est la première vérification
                if clean_url not in api_status:
                    api_status[clean_url] = {
                        'name': api_name,
                        'status': 'unknown',
                        'last_check': current_time,
                        'consecutive_failures': 0,
                        'last_ticket_created': None
                    }
                
                # Mettre à jour le statut
                api_status[clean_url]['last_check'] = current_time
                
                if is_healthy:
                    # API est UP
                    if api_status[clean_url]['status'] == 'down':
                        logger.info(f"🟢 API {api_name} ({clean_url}) est revenue UP")
                    api_status[clean_url]['status'] = 'up'
                    api_status[clean_url]['consecutive_failures'] = 0
                else:
                    # API est DOWN
                    api_status[clean_url]['consecutive_failures'] += 1
                    
                    # Créer un ticket seulement si c'est la première fois ou après plusieurs échecs
                    should_create_ticket = (
                        api_status[clean_url]['status'] != 'down' or  # Premier échec
                        api_status[clean_url]['consecutive_failures'] >= RETRY_ATTEMPTS  # Échecs consécutifs
                    )
                    
                    if should_create_ticket and api_status[clean_url]['last_ticket_created'] is None:
                        logger.warning(f"🔴 API {api_name} ({clean_url}) est DOWN: {message}")
                        result = create_jira_ticket('api_down', api_url=clean_url, api_name=api_name, error_message=message)
                        if result['success']:
                            api_status[clean_url]['last_ticket_created'] = current_time
                            logger.info(f"🎫 Ticket créé pour API DOWN {api_name}: {result['ticket_key']}")
                        else:
                            logger.error(f"❌ Échec création ticket pour {api_name}: {result['error']}")
                    
                    api_status[clean_url]['status'] = 'down'
                
                # Log de chaque vérification
                status_icon = "✅" if is_healthy else "❌"
                logger.info(f"{status_icon} {api_name} ({clean_url}): {message}")
            
            # Attendre avant la prochaine vérification
            logger.info(f"⏳ Attente de {HEALTH_CHECK_INTERVAL}s avant la prochaine vérification...")
            time.sleep(HEALTH_CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Erreur dans le monitoring worker: {str(e)}")
            time.sleep(HEALTH_CHECK_INTERVAL)

def start_monitoring():
    """
    Démarre le thread de monitoring
    """
    global monitoring_thread
    
    logger.info(f"Tentative de démarrage du monitoring...")
    logger.info(f"APIs configurées: {MONITORED_APIS}")
    
    if not MONITORED_APIS:
        logger.warning("Aucune API à monitorer configurée")
        return
    
    if monitoring_thread is None or not monitoring_thread.is_alive():
        try:
            monitoring_thread = threading.Thread(target=monitoring_worker, daemon=True)
            monitoring_thread.start()
            api_names = [api['name'] for api in MONITORED_APIS]
            logger.info(f"Monitoring démarré pour {len(MONITORED_APIS)} API(s): {', '.join(api_names)}")
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du monitoring: {str(e)}")
    else:
        logger.info("Monitoring déjà actif")

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de santé pour vérifier que le service fonctionne
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "jira_configured": bool(JIRA_URL and JIRA_USERNAME and JIRA_API_TOKEN and JIRA_PROJECT_KEY),
        "monitoring_active": monitoring_thread is not None and monitoring_thread.is_alive(),
        "monitored_apis": len(MONITORED_APIS),
        "api_status": api_status
    })

@app.route('/', methods=['GET'])
def home():
    """
    Page d'accueil avec des informations sur le service
    """
    return jsonify({
        "service": "Jira Webhook for API Monitoring",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "monitoring_status": "/monitoring/status",
            "start_monitoring": "/monitoring/start"
        },
        "status": "running",
        "monitoring_active": monitoring_thread is not None and monitoring_thread.is_alive()
    })

@app.route('/monitoring/status', methods=['GET'])
def monitoring_status():
    """
    Endpoint pour voir le statut du monitoring des APIs
    """
    return jsonify({
        "monitoring_active": monitoring_thread is not None and monitoring_thread.is_alive(),
        "monitored_apis": MONITORED_APIS,
        "api_status": api_status,
        "config": {
            "health_check_interval": HEALTH_CHECK_INTERVAL,
            "timeout": TIMEOUT,
            "retry_attempts": RETRY_ATTEMPTS,
            "ticket_summary_prefix": TICKET_SUMMARY_PREFIX,
            "ticket_description_message": TICKET_DESCRIPTION_MESSAGE
        }
    })

@app.route('/monitoring/start', methods=['POST'])
def start_monitoring_endpoint():
    """
    Endpoint pour démarrer le monitoring manuellement
    """
    start_monitoring()
    return jsonify({
        "message": "Monitoring démarré",
        "monitored_apis": MONITORED_APIS
    })

if __name__ == '__main__':
    # Vérification de la configuration au démarrage
    required_vars = ['JIRA_URL', 'JIRA_USERNAME', 'JIRA_API_TOKEN', 'JIRA_PROJECT_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")
        exit(1)
    
    logger.info("Démarrage du service de monitoring d'APIs")
    
    # Démarrer le monitoring si des APIs sont configurées
    start_monitoring()
    
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('DEBUG', 'False').lower() == 'true')
