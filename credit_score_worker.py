import logging
import time
from typing import Optional
from pyzeebe import ZeebeWorker, create_insecure_channel, create_oauth2_client_credentials_channel
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from dotenv import load_dotenv
import asyncio

# Lade Umgebungsvariablen
load_dotenv()

# Konfiguriere strukturiertes Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('credit_score_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Erstelle Zeebe Channel und Worker
def create_zeebe_worker():
    """Erstellt einen ZeebeWorker mit den entsprechenden Credentials."""
    zeebe_address = os.getenv("ZEEBE_ADDRESS")
    client_id = os.getenv("ZEEBE_CLIENT_ID")
    client_secret = os.getenv("ZEEBE_CLIENT_SECRET")
    authorization_server = os.getenv("ZEEBE_AUTHORIZATION_SERVER")
    audience = os.getenv("ZEEBE_TOKEN_AUDIENCE")
    
    if not all([zeebe_address, client_id, client_secret, authorization_server, audience]):
        logger.error("Nicht alle Zeebe-Umgebungsvariablen sind gesetzt!")
        raise ValueError("Fehlende Zeebe-Konfiguration in .env Datei")
    
    logger.info(f"Verbinde mit Zeebe unter: {zeebe_address}")
    
    # Erstelle OAuth2 Channel für Camunda Cloud
    channel = create_oauth2_client_credentials_channel(
        grpc_address=zeebe_address,
        client_id=client_id,
        client_secret=client_secret,
        authorization_server=authorization_server,
        audience=audience
    )
    
    return ZeebeWorker(channel)

# Worker wird später in der async Funktion erstellt
worker = None

# Konfiguration
JSON_SERVER_BASE_URL = os.getenv("JSON_SERVER_BASE_URL", "http://localhost:3000")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "1"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

def create_requests_session() -> requests.Session:
    """Erstellt eine Session mit Retry-Strategie für HTTP-Requests."""
    session = requests.Session()
    
    # Retry-Strategie konfigurieren
    retry_strategy = Retry(
        total=MAX_RETRIES,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=RETRY_BACKOFF_FACTOR,
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def fetch_credit_score(customer_id: str, session: requests.Session) -> Optional[dict]:
    """
    Ruft die Kreditwürdigkeit eines Kunden vom JSON-Server ab.
    
    Args:
        customer_id: Die eindeutige Kunden-ID
        session: Die HTTP-Session mit Retry-Logik
        
    Returns:
        Dict mit Kreditwürdigkeitsdaten oder None bei Fehlern
    """
    url = f"{JSON_SERVER_BASE_URL}/credit_scores/{customer_id}"
    
    try:
        logger.info(f"Sende Request an JSON-Server: {url}")
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Erfolgreiche Antwort vom JSON-Server für Kunde {customer_id}: {data}")
        
        # Validiere Antwortformat
        if not isinstance(data, dict) or "creditworthy" not in data or "score" not in data:
            logger.error(f"Ungültiges Antwortformat vom JSON-Server: {data}")
            return None
            
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout beim Aufruf des JSON-Servers für Kunde {customer_id}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Verbindungsfehler zum JSON-Server für Kunde {customer_id}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP-Fehler beim Aufruf des JSON-Servers für Kunde {customer_id}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Allgemeiner Request-Fehler für Kunde {customer_id}: {e}")
        return None
    except ValueError as e:
        logger.error(f"JSON-Dekodierungsfehler für Kunde {customer_id}: {e}")
        return None

def check_credit_score_handler(customer_id: str) -> dict:
    """
    Prüft die Kreditwürdigkeit eines Kunden.
    
    Diese Funktion wird von Camunda aufgerufen und:
    1. Ruft die Kreditwürdigkeitsdaten vom JSON-Server ab
    2. Gibt die Ergebnisse zurück an Camunda
    3. Behandelt Fehler graceful mit Fallback-Werten
    
    Args:
        customer_id: Die eindeutige Kunden-ID aus dem Camunda-Prozess
        
    Returns:
        Dict mit creditworthy (bool) und score (int)
    """
    logger.info(f"Starte Kreditwürdigkeitsprüfung für Kunde: {customer_id}")
    
    # Erstelle Session mit Retry-Logik
    session = create_requests_session()
    
    # Rufe Kreditwürdigkeitsdaten ab
    credit_data = fetch_credit_score(customer_id, session)
    
    if credit_data:
        result = {
            "creditworthy": bool(credit_data["creditworthy"]),
            "score": int(credit_data["score"])
        }
        logger.info(f"Kreditwürdigkeitsprüfung erfolgreich für Kunde {customer_id}: {result}")
        return result
    else:
        # Fallback bei Fehlern
        result = {
            "creditworthy": False,
            "score": 0
        }
        logger.warning(f"Kreditwürdigkeitsprüfung fehlgeschlagen für Kunde {customer_id}, verwende Fallback-Werte: {result}")
        return result

async def main():
    """Hauptfunktion die den Worker erstellt und startet."""
    logger.info("Starte Camunda Worker für Kreditwürdigkeitsprüfung...")
    logger.info(f"JSON-Server URL: {JSON_SERVER_BASE_URL}")
    logger.info(f"Max Retries: {MAX_RETRIES}")
    logger.info(f"Request Timeout: {REQUEST_TIMEOUT}s")
    
    try:
        # Erstelle Worker in der async Funktion
        worker = create_zeebe_worker()
        
        # Registriere Task Handler
        worker.task(task_type="check_credit_score")(check_credit_score_handler)
        
        logger.info("Worker erfolgreich erstellt, starte Verarbeitung...")
        await worker.work()
    except ValueError as e:
        logger.error(f"Konfigurationsfehler: {e}")
        logger.error("Bitte überprüfen Sie die .env Datei")
        raise
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Starten des Workers: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker wurde durch Benutzer beendet")
    except Exception as e:
        logger.error(f"Fehler beim Starten: {e}")
        raise
