#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion à Jira
"""
import requests
import base64
import json
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_jira_connection():
    """
    Teste la connexion à Jira avec les credentials configurés
    """
    # Configuration depuis les variables d'environnement
    jira_url = os.getenv('JIRA_URL', 'https://jiraprod.eid.local')
    jira_username = os.getenv('JIRA_USERNAME')
    jira_password = os.getenv('JIRA_API_TOKEN')
    jira_project_key = os.getenv('JIRA_PROJECT_KEY', 'TEST')
    jira_issue_type = os.getenv('JIRA_ISSUE_TYPE', 'Incident')
    
    if not all([jira_url, jira_username, jira_password, jira_project_key]):
        print("❌ Configuration incomplète. Vérifiez votre fichier .env")
        return False
    
    # Headers d'authentification
    credentials = f"{jira_username}:{jira_password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔗 Test de connexion à Jira: {jira_url}")
    print(f"👤 Utilisateur: {jira_username}")
    print(f"📋 Projet: {jira_project_key}")
    print(f"🎫 Type de ticket: {jira_issue_type}")
    print("-" * 50)
    
    # Test 1: Vérifier l'authentification
    print("1️⃣ Test d'authentification...")
    try:
        response = requests.get(f"{jira_url}/rest/api/2/myself", headers=headers, timeout=10)
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Authentification réussie: {user_info.get('displayName', 'Unknown')}")
        else:
            print(f"❌ Échec de l'authentification: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return False
    
    # Test 2: Vérifier l'accès au projet
    print("\n2️⃣ Test d'accès au projet...")
    try:
        response = requests.get(f"{jira_url}/rest/api/2/project/{jira_project_key}", headers=headers, timeout=10)
        if response.status_code == 200:
            project_info = response.json()
            print(f"✅ Projet accessible: {project_info.get('name', 'Unknown')}")
        else:
            print(f"❌ Projet inaccessible: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur d'accès au projet: {str(e)}")
        return False
    
    # Test 3: Créer un ticket de test
    print("\n3️⃣ Test de création de ticket...")
    test_ticket = {
        "fields": {
            "project": {
                "key": jira_project_key
            },
            "summary": "[TEST] Test de connexion webhook",
            "description": "Ce ticket a été créé automatiquement pour tester la connexion du webhook Jira.",
            "issuetype": {
                "name": jira_issue_type
            }
        }
    }
    
    try:
        response = requests.post(
            f"{jira_url}/rest/api/2/issue",
            headers=headers,
            json=test_ticket,
            timeout=10
        )
        
        if response.status_code == 201:
            ticket_data = response.json()
            ticket_key = ticket_data['key']
            ticket_url = f"{jira_url}/browse/{ticket_key}"
            print(f"✅ Ticket de test créé avec succès!")
            print(f"   🎫 Clé: {ticket_key}")
            print(f"   🔗 URL: {ticket_url}")
            
            # Optionnel: Fermer le ticket de test
            print("\n4️⃣ Fermeture du ticket de test...")
            close_data = {
                "transition": {
                    "name": "Close"
                }
            }
            close_response = requests.post(
                f"{jira_url}/rest/api/2/issue/{ticket_key}/transitions",
                headers=headers,
                json=close_data,
                timeout=10
            )
            
            if close_response.status_code == 204:
                print("✅ Ticket de test fermé")
            else:
                print(f"⚠️  Impossible de fermer le ticket: {close_response.status_code}")
            
            return True
        else:
            print(f"❌ Échec de création du ticket: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du ticket: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Test de connexion Jira pour le webhook")
    print("=" * 50)
    
    success = test_jira_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tous les tests sont passés! Votre configuration Jira est correcte.")
    else:
        print("💥 Certains tests ont échoué. Vérifiez votre configuration.")
        print("\n💡 Conseils:")
        print("   - Vérifiez que votre fichier .env est correctement configuré")
        print("   - Vérifiez que vos credentials Jira sont valides")
        print("   - Vérifiez que vous avez accès au projet spécifié")
        print("   - Vérifiez que l'URL Jira est accessible depuis votre machine")
