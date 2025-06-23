import logging
import os
import asyncio
from pyzeebe import ZeebeClient, create_insecure_channel, create_oauth2_client_credentials_channel, ZeebeWorker
from dotenv import load_dotenv
from grpc import ssl_channel_credentials, metadata_call_credentials, composite_channel_credentials
import grpc

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log loaded environment variables for debugging
logger.info(f"Loaded ENV: ZEEBE_ADDRESS={os.getenv('ZEEBE_ADDRESS')}")
logger.info(f"Loaded ENV: ZEEBE_CLIENT_ID={os.getenv('ZEEBE_CLIENT_ID')}")
logger.info(f"Loaded ENV: ZEEBE_CLIENT_SECRET={os.getenv('ZEEBE_CLIENT_SECRET')}")
logger.info(f"Loaded ENV: ZEEBE_AUTHORIZATION_SERVER={os.getenv('ZEEBE_AUTHORIZATION_SERVER')}")
logger.info(f"Loaded ENV: ZEEBE_TOKEN_AUDIENCE={os.getenv('ZEEBE_TOKEN_AUDIENCE')}")

# Support both old and new env variable names for Camunda Cloud
ZEEBE_ADDRESS = os.getenv("ZEEBE_ADDRESS") or os.getenv("ZEEBE_GRPC_ADDRESS")
ZEEBE_CLIENT_ID = os.getenv("ZEEBE_CLIENT_ID") or os.getenv("CAMUNDA_CLIENT_ID") or os.getenv("CAMUNDA_CLIENT_AUTH_CLIENTID")
ZEEBE_CLIENT_SECRET = os.getenv("ZEEBE_CLIENT_SECRET") or os.getenv("CAMUNDA_CLIENT_SECRET") or os.getenv("CAMUNDA_CLIENT_AUTH_CLIENTSECRET")
ZEEBE_AUTHORIZATION_SERVER = os.getenv("ZEEBE_AUTHORIZATION_SERVER") or os.getenv("ZEEBE_AUTHORIZATION_SERVER_URL") or os.getenv("CAMUNDA_OAUTH_URL")
ZEEBE_TOKEN_AUDIENCE = os.getenv("ZEEBE_TOKEN_AUDIENCE")

# Zeebe connection setup
def create_zeebe_client():
    # Prüfe, ob ein Access Token manuell gesetzt wurde
    access_token = os.getenv("ZEEBE_ACCESS_TOKEN")
    if not access_token:
        access_token = input("Bitte gib deinen Zeebe Access Token ein: ").strip()
    if access_token:
        logger.info("Nutze manuell eingegebenen Access Token für die Verbindung.")
        # Baue einen gRPC-Channel mit Token
        def token_callback(context, callback):
            callback([('authorization', f'Bearer {access_token}')], None)
        creds = composite_channel_credentials(
            ssl_channel_credentials(),
            metadata_call_credentials(token_callback)
        )
        # Adresse muss ohne grpcs:// sein
        address = ZEEBE_ADDRESS.replace('grpcs://', '') if ZEEBE_ADDRESS else ZEEBE_ADDRESS
        channel = grpc.aio.secure_channel(address, creds)
        return ZeebeClient(channel)
    logger.info(f"Connecting with: ZEEBE_ADDRESS={ZEEBE_ADDRESS}")
    logger.info(f"Connecting with: ZEEBE_CLIENT_ID={ZEEBE_CLIENT_ID}")
    logger.info(f"Connecting with: ZEEBE_CLIENT_SECRET={ZEEBE_CLIENT_SECRET}")
    logger.info(f"Connecting with: ZEEBE_AUTHORIZATION_SERVER={ZEEBE_AUTHORIZATION_SERVER}")
    logger.info(f"Connecting with: ZEEBE_TOKEN_AUDIENCE={ZEEBE_TOKEN_AUDIENCE}")
    if not all([ZEEBE_ADDRESS, ZEEBE_CLIENT_ID, ZEEBE_CLIENT_SECRET, ZEEBE_AUTHORIZATION_SERVER, ZEEBE_TOKEN_AUDIENCE]):
        logger.error("Missing Zeebe environment variables!")
        raise ValueError("Missing Zeebe configuration in .env file")
    # Strip whitespace from all variables (common .env issue)
    address = ZEEBE_ADDRESS.strip() if ZEEBE_ADDRESS else ZEEBE_ADDRESS
    client_id = ZEEBE_CLIENT_ID.strip() if ZEEBE_CLIENT_ID else ZEEBE_CLIENT_ID
    client_secret = ZEEBE_CLIENT_SECRET.strip() if ZEEBE_CLIENT_SECRET else ZEEBE_CLIENT_SECRET
    auth_server = ZEEBE_AUTHORIZATION_SERVER.strip() if ZEEBE_AUTHORIZATION_SERVER else ZEEBE_AUTHORIZATION_SERVER
    audience = ZEEBE_TOKEN_AUDIENCE.strip() if ZEEBE_TOKEN_AUDIENCE else ZEEBE_TOKEN_AUDIENCE
    channel = create_oauth2_client_credentials_channel(
        grpc_address=address,
        client_id=client_id,
        client_secret=client_secret,
        authorization_server=auth_server,
        audience=audience
    )
    return ZeebeClient(channel)

def create_zeebe_worker():
    access_token = os.getenv("ZEEBE_ACCESS_TOKEN")
    if not access_token:
        access_token = input("Bitte gib deinen Zeebe Access Token ein: ").strip()
    if access_token:
        logger.info("Nutze manuell eingegebenen Access Token für die Verbindung (Worker).")
        def token_callback(context, callback):
            callback([('authorization', f'Bearer {access_token}')], None)
        creds = composite_channel_credentials(
            ssl_channel_credentials(),
            metadata_call_credentials(token_callback)
        )
        address = ZEEBE_ADDRESS.replace('grpcs://', '') if ZEEBE_ADDRESS else ZEEBE_ADDRESS
        channel = grpc.aio.secure_channel(address, creds)
        return ZeebeWorker(channel)
    logger.info(f"Connecting with: ZEEBE_ADDRESS={ZEEBE_ADDRESS}")
    logger.info(f"Connecting with: ZEEBE_CLIENT_ID={ZEEBE_CLIENT_ID}")
    logger.info(f"Connecting with: ZEEBE_CLIENT_SECRET={ZEEBE_CLIENT_SECRET}")
    logger.info(f"Connecting with: ZEEBE_AUTHORIZATION_SERVER={ZEEBE_AUTHORIZATION_SERVER}")
    logger.info(f"Connecting with: ZEEBE_TOKEN_AUDIENCE={ZEEBE_TOKEN_AUDIENCE}")
    if not all([ZEEBE_ADDRESS, ZEEBE_CLIENT_ID, ZEEBE_CLIENT_SECRET, ZEEBE_AUTHORIZATION_SERVER, ZEEBE_TOKEN_AUDIENCE]):
        logger.error("Missing Zeebe environment variables!")
        raise ValueError("Missing Zeebe configuration in .env file")
    channel = create_oauth2_client_credentials_channel(
        grpc_address=ZEEBE_ADDRESS,
        client_id=ZEEBE_CLIENT_ID,
        client_secret=ZEEBE_CLIENT_SECRET,
        authorization_server=ZEEBE_AUTHORIZATION_SERVER,
        audience=ZEEBE_TOKEN_AUDIENCE
    )
    return ZeebeWorker(channel)

INCOMING_EVENT = os.getenv("INCOMING_EVENT", "incoming_event")
OUTGOING_EVENT = os.getenv("OUTGOING_EVENT", "outgoing_event")
JOB_TYPE = os.getenv("JOB_TYPE", "forward_message")

async def forward_message(client: ZeebeClient, message: dict):
    """
    Forwards the incoming message payload to another process as a new message event.
    """
    logger.info(f"Forwarding message: {message}")
    # You can transform the payload here if needed
    await client.publish_message(
        name=OUTGOING_EVENT,
        correlation_key=message.get("correlationKey", "default-key"),
        variables=message.get("variables", message)
    )
    logger.info(f"Published outgoing message event '{OUTGOING_EVENT}'")

async def forward_message_job(variables: dict) -> dict:
    """
    Zeebe Job Handler: Receives variables from a service task and forwards them as a message event.
    """
    logger.info(f"Received job with variables: {variables}")
    # Forward as message event
    await worker._client.publish_message(
        name=OUTGOING_EVENT,
        correlation_key=variables.get("correlationKey", "default-key"),
        variables=variables
    )
    logger.info(f"Published outgoing message event '{OUTGOING_EVENT}' with variables: {variables}")
    return {}

async def main():
    logger.info("Starting message forwarder worker (Service Task mode)...")
    global worker
    worker = create_zeebe_worker()
    worker.task(task_type=JOB_TYPE)(forward_message_job)
    logger.info(f"Worker registered for job type: {JOB_TYPE}")
    await worker.work()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
    except Exception as e:
        logger.error(f"Error in worker: {e}")
        raise
