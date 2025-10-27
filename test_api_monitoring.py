#!/usr/bin/env python3
"""
Script de test pour le monitoring des APIs
"""
import requests
import time
import json

def test_api_monitoring():
    """
    Teste le monitoring des APIs
    """
    base_url = "http://localhost:5000"
    
    print("🧪 Test du monitoring des APIs")
    print("=" * 50)
    
    # Test 1: Vérifier que le service fonctionne
    print("1️⃣ Test de santé du service...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service en marche: {health_data['status']}")
            print(f"   - Monitoring actif: {health_data.get('monitoring_active', False)}")
            print(f"   - APIs monitorées: {health_data.get('monitored_apis', 0)}")
        else:
            print(f"❌ Service en erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossible de joindre le service: {str(e)}")
        return False
    
    # Test 2: Vérifier le statut du monitoring
    print("\n2️⃣ Test du statut du monitoring...")
    try:
        response = requests.get(f"{base_url}/monitoring/status", timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Monitoring actif: {status_data['monitoring_active']}")
            print(f"   - APIs configurées: {len(status_data['monitored_apis'])}")
            
            if status_data['monitored_apis']:
                print("   - APIs monitorées:")
                for api in status_data['monitored_apis']:
                    print(f"     • {api['name']} ({api['url']})")
            
            if status_data['api_status']:
                print("   - Statut des APIs:")
                for url, status in status_data['api_status'].items():
                    print(f"     • {status.get('name', 'Unknown')}: {status['status']}")
        else:
            print(f"❌ Erreur statut monitoring: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur statut monitoring: {str(e)}")
    
    # Test 3: Démarrer le monitoring manuellement
    print("\n3️⃣ Test de démarrage du monitoring...")
    try:
        response = requests.post(f"{base_url}/monitoring/start", timeout=5)
        if response.status_code == 200:
            start_data = response.json()
            print(f"✅ Monitoring démarré: {start_data['message']}")
            print(f"   - APIs: {len(start_data['monitored_apis'])}")
        else:
            print(f"❌ Erreur démarrage: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur démarrage: {str(e)}")
    
    # Test 4: Vérifier la page d'accueil
    print("\n4️⃣ Test de la page d'accueil...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            home_data = response.json()
            print(f"✅ Page d'accueil accessible")
            print(f"   - Service: {home_data['service']}")
            print(f"   - Version: {home_data['version']}")
            print(f"   - Monitoring actif: {home_data.get('monitoring_active', False)}")
        else:
            print(f"❌ Erreur page d'accueil: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur page d'accueil: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Tests terminés!")
    print("\n💡 Pour tester avec de vraies APIs:")
    print("   1. Configurez MONITORED_APIS dans votre .env")
    print("   2. Redémarrez le service")
    print("   3. Vérifiez les logs: docker-compose logs -f")

if __name__ == "__main__":
    test_api_monitoring()
