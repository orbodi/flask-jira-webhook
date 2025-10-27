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

## Configuration Prometheus

Ajoutez cette configuration dans votre `prometheus.yml` :

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

rule_files:
  - "alert_rules.yml"

# Exemple de règle d'alerte
groups:
  - name: example
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
```

Et dans votre `alertmanager.yml` :

```yaml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'jira-webhook'

receivers:
  - name: 'jira-webhook'
    webhook_configs:
      - url: 'http://your-webhook-server:5000/webhook/prometheus'
        send_resolved: true
```

## Endpoints API

### POST /webhook/prometheus
Reçoit les alertes Prometheus et crée des tickets Jira.

**Exemple de payload :**
```json
{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighErrorRate",
        "severity": "critical"
      },
      "annotations": {
        "summary": "High error rate detected",
        "description": "Error rate is 0.15 errors per second"
      }
    }
  ]
}
```

### GET /health
Vérifie l'état de santé du service et du monitoring.

**Réponse :**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "jira_configured": true,
  "monitoring_active": true,
  "monitored_apis": 2,
  "api_status": {
    "http://api1.example.com": {
      "status": "up",
      "last_check": "2024-01-01T12:00:00.000Z",
      "consecutive_failures": 0
    }
  }
}
```

### GET /monitoring/status
Affiche le statut détaillé du monitoring des APIs.

**Réponse :**
```json
{
  "monitoring_active": true,
  "monitored_apis": ["http://api1.example.com", "http://api2.example.com"],
  "api_status": {
    "http://api1.example.com": {
      "status": "up",
      "last_check": "2024-01-01T12:00:00.000Z",
      "consecutive_failures": 0,
      "last_ticket_created": null
    }
  },
  "config": {
    "health_check_interval": 30,
    "timeout": 10,
    "retry_attempts": 3
  }
}
```

### POST /monitoring/start
Démarre manuellement le monitoring des APIs.

### GET /
Page d'accueil avec informations sur le service.

## Monitoring des APIs Spring Boot

Le webhook peut maintenant **monitorer activement** vos APIs Spring Boot et créer automatiquement des tickets Jira quand elles sont down.

### Configuration du monitoring

1. **Ajoutez vos APIs dans `.env`** :
```bash
# Format: URL|NOM_API,URL|NOM_API
MONITORED_APIS=http://api1.example.com|User-Service,http://api2.example.com:8080|Payment-Service,http://api3.example.com:9000|Notification-Service
```

2. **Configurez les paramètres de monitoring** :
```bash
HEALTH_CHECK_INTERVAL=30    # Vérification toutes les 30 secondes
HEALTH_CHECK_TIMEOUT=10     # Timeout de 10 secondes
HEALTH_CHECK_RETRY=3        # 3 tentatives avant création de ticket
```

3. **Personnalisez les tickets créés** (optionnel) :
```bash
TICKET_PRIORITY_API_DOWN=High
TICKET_LABELS_API_DOWN=api-monitoring,spring-boot,critical,downtime
TICKET_ASSIGNEE_API_DOWN=john.doe
TICKET_COMPONENTS_API_DOWN=Backend,API,Monitoring
```

### Comment ça fonctionne

1. **Health Check automatique** : Le webhook appelle `/actuator/health` de chaque API
2. **Détection de downtime** : Si l'API ne répond pas ou retourne un statut != "UP"
3. **Création de ticket** : Un ticket Jira est créé automatiquement avec :
   - Priorité **High**
   - Labels : `api-monitoring`, `spring-boot`, `critical`, `downtime`
   - Description détaillée avec actions recommandées

### Exemple de ticket créé

```
[CRITICAL] API DOWN - User-Service

API Monitoring Alert
- API Name: User-Service
- API URL: http://api1.example.com
- Status: DOWN
- Error: Connection Error
- Timestamp: 2024-01-01T12:00:00.000Z
- Health Check Endpoint: http://api1.example.com/actuator/health

Détails techniques:
- L'API Spring Boot ne répond plus aux health checks
- Vérifiez la disponibilité du service
- Consultez les logs de l'application Spring Boot

Actions recommandées:
1. Vérifier les logs de l'application
2. Redémarrer le service si nécessaire
3. Vérifier les ressources système (CPU, mémoire, disque)
4. Contrôler la connectivité réseau
```

**Configuration du ticket :**
- **Priorité** : High (configurable)
- **Labels** : api-monitoring, spring-boot, critical, downtime (configurables)
- **Assigné** : john.doe (optionnel)
- **Composants** : Backend, API, Monitoring (optionnels)

## Mapping des sévérités

| Sévérité Prometheus | Priorité Jira | Labels |
|-------------------|---------------|---------|
| critical          | High          | prometheus, alert, critical |
| high              | High          | prometheus, alert, high |
| medium            | Medium        | prometheus, alert, medium |
| low               | Medium        | prometheus, alert, low |
| warning           | Medium        | prometheus, alert, warning |

| Type d'alerte | Priorité Jira | Labels |
|---------------|---------------|---------|
| API DOWN      | High          | api-monitoring, spring-boot, critical, downtime |

## Logs

L'application génère des logs détaillés pour :
- Réception des alertes
- Création des tickets Jira
- Erreurs de configuration
- Erreurs de communication avec Jira

## Dépannage

### Vérifier la configuration
```bash
curl http://localhost:5000/health
```

### Tester le webhook
```bash
curl -X POST http://localhost:5000/webhook/prometheus \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "TestAlert",
        "severity": "critical"
      },
      "annotations": {
        "summary": "Test alert",
        "description": "This is a test alert"
      }
    }]
  }'
```

### Tester le monitoring des APIs
```bash
# Vérifier le statut du monitoring
curl http://localhost:5000/monitoring/status

# Démarrer le monitoring manuellement
curl -X POST http://localhost:5000/monitoring/start
```

### Vérifier les logs
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f jira-webhook
```

## Sécurité

- L'application utilise l'authentification Basic avec token API Jira
- Les credentials sont stockés dans des variables d'environnement
- L'application s'exécute avec un utilisateur non-root dans Docker
- Aucune donnée sensible n'est loggée

## Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request
