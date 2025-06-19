"""
Test-Script für den Credit Score Worker
Testet die Verbindung zum JSON-Server und die Kreditwürdigkeitsprüfung
"""

import logging
import sys
import os
from dotenv import load_dotenv
import requests

# Lade Umgebungsvariablen
load_dotenv()

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_json_server_connection():
    """Testet die Verbindung zum JSON-Server."""
    base_url = os.getenv("JSON_SERVER_BASE_URL", "http://localhost:3000")
    
    try:
        # Teste grundlegende Erreichbarkeit
        response = requests.get(f"{base_url}/health", timeout=5)
        logger.info(f"JSON-Server ist erreichbar: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"JSON-Server ist nicht erreichbar: {e}")
        return False

def test_credit_score_endpoint(customer_id="12345"):
    """Testet den Credit Score Endpoint."""
    base_url = os.getenv("JSON_SERVER_BASE_URL", "http://localhost:3000")
    
    try:
        response = requests.get(f"{base_url}/credit_scores/{customer_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Credit Score Daten für Kunde {customer_id}: {data}")
            return True
        else:
            logger.warning(f"Credit Score Endpoint antwortet mit Status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Fehler beim Testen des Credit Score Endpoints: {e}")
        return False

def main():
    """Führt alle Tests aus."""
    logger.info("Starte Tests für Credit Score Worker...")
    
    # Test 1: JSON-Server Verbindung
    logger.info("Test 1: JSON-Server Verbindung")
    if not test_json_server_connection():
        logger.error("JSON-Server Test fehlgeschlagen. Bitte starten Sie den JSON-Server.")
        sys.exit(1)
    
    # Test 2: Credit Score Endpoint
    logger.info("Test 2: Credit Score Endpoint")
    if not test_credit_score_endpoint():
        logger.error("Credit Score Endpoint Test fehlgeschlagen.")
        sys.exit(1)
    
    logger.info("Alle Tests erfolgreich! Der Worker ist bereit.")

if __name__ == "__main__":
    main()
