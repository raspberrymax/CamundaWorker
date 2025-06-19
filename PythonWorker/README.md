# Camunda 8 Credit Score Worker

Dieser Worker ist Teil eines Camunda 8 BPMN-Prozesses zur Kreditvergabe und übernimmt die automatische Prüfung der Kreditwürdigkeit eines Kunden anhand von lokal simulierten Daten.

## 🎯 Funktionsweise

1. Der Worker wird in Camunda als Service Task mit dem Typ `check_credit_score` eingebunden
2. Camunda übermittelt dem Worker eine Kunden-ID
3. Der Worker ruft einen lokalen JSON-Server (http://localhost:3000) auf, um die Kreditwürdigkeit abzurufen
4. Die Antwort enthält z.B. `creditworthy: true` und `score: 750`
5. Der Worker gibt die Daten zurück an Camunda, wo die nächsten Prozessschritte davon abhängen

## 🚀 Setup

### 1. Python-Umgebung einrichten

```powershell
# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
.\venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### 2. Umgebungsvariablen konfigurieren

Die `.env` Datei enthält bereits alle notwendigen Konfigurationen:

- **Camunda Cloud Konfiguration**: Client-ID, Secret, Cluster-ID, Region
- **JSON-Server Konfiguration**: Base URL
- **HTTP-Request Konfiguration**: Retries, Timeouts

### 3. JSON-Server starten

Für die Tests muss ein JSON-Server auf `http://localhost:3000` laufen, der Credit Score Daten bereitstellt.

Beispiel-Endpoint: `GET /credit_scores/{customer_id}`

Erwartete Antwort:
```json
{
  "creditworthy": true,
  "score": 750
}
```

### 4. Worker testen

```powershell
# Test-Script ausführen (optional)
python test_worker.py

# Worker starten
python credit_score_worker.py
```

## 🔧 Verbesserungen

### ✅ Implementiert

- **Konfiguration für Camunda Cloud**: Client-ID, Secret, Cluster-ID, Region
- **Worker Registrierung**: Task-Type `check_credit_score`
- **Datenübertragung**: Kunden-ID empfangen
- **JSON-Server Integration**: GET-Request an `/credit_scores/{customer_id}`
- **Datenrückgabe**: Antwort auswerten und an Camunda zurückgeben
- **🆕 Fehlerbehandlung**: Umfassende Retry-Logik mit exponential backoff
- **🆕 Strukturiertes Logging**: Logging in Datei und Konsole mit verschiedenen Log-Leveln

### 🔧 Neue Features

#### Retry-Mechanismus
- **Automatische Wiederholung**: Bei Netzwerkfehlern (HTTP 429, 5xx)
- **Exponential Backoff**: Zunehmende Wartezeiten zwischen Versuchen
- **Konfigurierbar**: Anzahl Retries und Backoff-Faktor über Umgebungsvariablen

#### Strukturiertes Logging
- **Dateimäßiges Logging**: Logs werden in `credit_score_worker.log` gespeichert
- **Konsolen-Output**: Gleichzeitige Ausgabe in der Konsole
- **Log-Level**: INFO, WARNING, ERROR für verschiedene Ereignisse
- **Strukturierte Nachrichten**: Zeitstempel, Logger-Name, Level und Nachricht

#### Robuste Fehlerbehandlung
- **Timeout-Behandlung**: Konfigurierbare Request-Timeouts
- **Verbindungsfehler**: Graceful Handling von Netzwerkproblemen
- **JSON-Validierung**: Überprüfung der Antwortstruktur
- **Fallback-Verhalten**: Sichere Standardwerte bei Fehlern

## 📋 Konfiguration

### Umgebungsvariablen (.env)

```env
# Camunda Zeebe Configuration
ZEEBE_ADDRESS=https://your-cluster.bru-2.zeebe.camunda.io:443
ZEEBE_CLIENT_ID=your-client-id
ZEEBE_CLIENT_SECRET=your-client-secret
ZEEBE_AUTHORIZATION_SERVER=https://login.cloud.camunda.io/oauth/token
ZEEBE_TOKEN_AUDIENCE=zeebe.camunda.io

# JSON Server Configuration
JSON_SERVER_BASE_URL=http://localhost:3000

# HTTP Request Configuration
MAX_RETRIES=3                # Anzahl der Wiederholungsversuche
RETRY_BACKOFF_FACTOR=1       # Backoff-Faktor für exponential backoff
REQUEST_TIMEOUT=10           # Timeout in Sekunden
```

## 📊 Logging

Der Worker erstellt strukturierte Logs in:
- **Datei**: `credit_score_worker.log`
- **Konsole**: Für Debugging und Monitoring

Log-Beispiele:
```
2025-06-19 10:30:15,123 - __main__ - INFO - Starte Kreditwürdigkeitsprüfung für Kunde: 12345
2025-06-19 10:30:15,145 - __main__ - INFO - Sende Request an JSON-Server: http://localhost:3000/credit_scores/12345
2025-06-19 10:30:15,234 - __main__ - INFO - Erfolgreiche Antwort vom JSON-Server für Kunde 12345: {'creditworthy': True, 'score': 750}
```

## 🛠️ Troubleshooting

### Häufige Probleme

1. **JSON-Server nicht erreichbar**
   - Lösung: JSON-Server auf Port 3000 starten
   - Test: `python test_worker.py`

2. **Camunda Verbindungsfehler**
   - Lösung: Camunda Cloud Credentials in `.env` überprüfen

3. **Import-Fehler**
   - Lösung: Virtuelle Umgebung aktivieren und Dependencies installieren

### Debug-Modus

Für ausführlichere Logs, das Log-Level auf DEBUG setzen:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 📁 Dateien

- `credit_score_worker.py`: Hauptworker-Implementation
- `test_worker.py`: Test-Script für JSON-Server Verbindung
- `requirements.txt`: Python-Dependencies
- `.env`: Umgebungsvariablen und Konfiguration
- `README.md`: Diese Dokumentation
- `credit_score_worker.log`: Log-Datei (wird automatisch erstellt)

## 🔗 Camunda Integration

### BPMN Service Task Konfiguration

```xml
<bpmn:serviceTask id="checkCreditScore" name="Check Credit Score">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="check_credit_score" />
    <zeebe:ioMapping>
      <zeebe:input source="=customerId" target="customer_id" />
      <zeebe:output source="=creditworthy" target="creditworthy" />
      <zeebe:output source="=score" target="creditScore" />
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

### Prozessvariablen

**Input:**
- `customer_id` (string): Die eindeutige Kunden-ID

**Output:**
- `creditworthy` (boolean): Ist der Kunde kreditwürdig?
- `score` (integer): Credit Score (0-850)
