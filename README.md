# Jira Webhook pour Monitoring d'APIs

Webhook Flask qui **monitore activement** vos APIs Spring Boot et **crée automatiquement** des tickets Jira lors des pannes.

## ✨ Fonctionnalités principales

- 🎯 **Monitoring proactif** des APIs Spring Boot via `/actuator/health`
- 🚨 **Détection automatique** des pannes en temps réel
- 🎫 **Création automatique** de tickets Jira détaillés
- ⚙️ **Configuration flexible** (priorités, assignés, composants)
- 🐳 **Déploiement Docker** simple
- 📊 **Support Prometheus** (optionnel)

## Structure du projet

```
Jira-webhook/
├── app.py                    # Application Flask principale avec monitoring
├── requirements.txt          # Dépendances Python
├── Dockerfile               # Image Docker optimisée
├── docker-compose.yml       # Configuration Docker Compose
├── env.example              # Exemple de configuration
├── test_jira_connection.py  # Script de test de connexion Jira
├── .gitignore              # Fichiers à ignorer
└── README.md               # Documentation complète
```

## ⚙️ Configuration rapide

### 1. Variables essentielles

```bash
# Copier le template
cp env.example .env

# Configuration Jira
JIRA_URL=url-jira
JIRA_USERNAME=your-username
JIRA_API_TOKEN=your-password
JIRA_PROJECT_KEY=TEST

# APIs à monitorer (format: URL|NOM_API)
MONITORED_APIS=http://api1.com|User-Service,http://api2.com:8080|Payment-Service

# Personnalisation des tickets (optionnel)
TICKET_PRIORITY_API_DOWN=High
TICKET_ASSIGNEE_API_DOWN=john.doe
TICKET_LABELS_API_DOWN=api-monitoring,spring-boot,critical
```

### 2. Test de connexion

```bash
python test_jira_connection.py
```

## 🚀 Déploiement

### Docker Compose (Recommandé)

```bash
# 1. Configuration
cp env.example .env
# Éditer .env avec vos paramètres

# 2. Test (optionnel)
python test_jira_connection.py

# 3. Démarrage
docker-compose up -d

# 4. Vérification
docker-compose logs -f
```

### Installation locale

```bash
# Environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installation
pip install -r requirements.txt

# Configuration et démarrage
export JIRA_URL="url-jira"
export MONITORED_APIS="http://api1.com|User-Service"
python app.py
```

## 📊 Support Prometheus (désactivé pour les tests)

Le support Prometheus est temporairement désactivé pour se concentrer sur le monitoring des APIs.

## 🔌 Endpoints API

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | État de santé du service |
| `/monitoring/status` | GET | Statut détaillé du monitoring |
| `/monitoring/start` | POST | Démarre le monitoring |
| `/` | GET | Page d'accueil |

## 🎯 Monitoring des APIs

### Comment ça fonctionne

1. **Health Check automatique** : Appelle `/actuator/health` de chaque API
2. **Détection de downtime** : Si l'API ne répond pas ou status != "UP"
3. **Création de ticket** : Ticket Jira automatique avec détails complets

### Exemple de ticket créé

```
[CRITICAL] API DOWN - User-Service

API DOWN - User-Service

- URL: http://api1.example.com
- Error: Connection Error
- Time: 2024-01-01 12:00:00

L'API ne répond plus aux health checks
```

### Personnalisation des tickets

```bash
# Personnaliser le contenu des tickets
TICKET_SUMMARY_PREFIX=[URGENT] API DOWN
TICKET_DESCRIPTION_TITLE=Service indisponible
TICKET_DESCRIPTION_MESSAGE=Le service ne répond plus, intervention requise
```

## 🔧 Dépannage

### Vérifier la configuration
```bash
curl http://localhost:5000/health
```

### Tester le monitoring
```bash
# Statut du monitoring
curl http://localhost:5000/monitoring/status

# Démarrer manuellement
curl -X POST http://localhost:5000/monitoring/start
```

### Logs
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f jira-webhook
```

## 🔒 Sécurité

- Authentification Basic avec credentials Jira
- Variables d'environnement pour les secrets
- Utilisateur non-root dans Docker
- Aucune donnée sensible loggée
