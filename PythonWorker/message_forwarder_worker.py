import logging
import os
import asyncio
from pyzeebe import ZeebeClient, create_insecure_channel, create_oauth2_client_credentials_channel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('message_forwarder_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Zeebe connection setup
def create_zeebe_client():
    zeebe_address = os.getenv("ZEEBE_ADDRESS")
    client_id = os.getenv("ZEEBE_CLIENT_ID")
    client_secret = os.getenv("ZEEBE_CLIENT_SECRET")
    authorization_server = os.getenv("ZEEBE_AUTHORIZATION_SERVER")
    audience = os.getenv("ZEEBE_TOKEN_AUDIENCE")

    if not all([zeebe_address, client_id, client_secret, authorization_server, audience]):
        logger.error("Missing Zeebe environment variables!")
        raise ValueError("Missing Zeebe configuration in .env file")

    channel = create_oauth2_client_credentials_channel(
        grpc_address=zeebe_address,
        client_id=client_id,
        client_secret=client_secret,
        authorization_server=authorization_server,
        audience=audience
    )
    return ZeebeClient(channel)

INCOMING_EVENT = os.getenv("INCOMING_EVENT", "incoming_event")
OUTGOING_EVENT = os.getenv("OUTGOING_EVENT", "outgoing_event")

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

async def main():
    logger.info("Starting message forwarder worker...")
    client = create_zeebe_client()

    async def message_handler(message):
        await forward_message(client, message)

    logger.info(f"Listening for incoming message event: {INCOMING_EVENT}")
    # This is a simple polling loop; Zeebe Python SDK does not support message subscriptions directly
    # In a real-world scenario, you would use a process that triggers a job, or poll for messages
    while True:
        # This is a placeholder for actual message polling logic
        # Replace with your own mechanism to receive/process Zeebe messages
        await asyncio.sleep(10)
        # Example: message = await poll_for_message()
        # await message_handler(message)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
    except Exception as e:
        logger.error(f"Error in worker: {e}")
        raise
