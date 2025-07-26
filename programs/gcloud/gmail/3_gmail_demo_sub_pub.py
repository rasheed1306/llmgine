import json
import os

# AI: base64 import removed as the code using it is currently commented out.
# AI: Add 'import base64' back if you uncomment the email body decoding logic.
# import base64
import time
from typing import Any, Callable, Dict, List, Optional

from google.auth.transport.requests import Request
from google.cloud import pubsub_v1

# AI: Google Cloud & API client libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

# AI: Define types for better readability
type ProjectId = str
type TopicName = str
type SubscriptionName = str
type EmailAddress = str
type GmailMessage = Dict[str, Any]
type PubSubMessage = Any  # google.cloud.pubsub_v1.subscriber.message.Message

# AI: --- Configuration ---
# AI: Replace with your actual Project ID, Topic name, and Subscription name
# AI: These should match what you used/got from 1_setup.sh
GCP_PROJECT_ID: ProjectId = "darcy-457705"  # e.g., "my-gcp-project-123"
PUB_SUB_TOPIC_NAME: TopicName = (
    "gmail-notifications"  # e.g., "gmail-notifications" (just the name, not full path)
)
PUB_SUB_SUBSCRIPTION_NAME: SubscriptionName = (
    "gmail-subscriber"  # e.g., "gmail-subscriber"
)

# AI: List of email IDs you want to monitor for replies
# AI: Important: This script currently checks the "From" header.
# AI: If you are looking for replies *to* these emails, the logic in process_email might need adjustment
# AI: to check "To", "Cc", or "In-Reply-To" / "References" headers.
TARGET_EMAIL_IDS: List[EmailAddress] = [
    "ai@dscubed.org.au",
]

FOLDER: str = "gcloud/gmail"

# AI: Path to your OAuth 2.0 credentials JSON file
CREDENTIALS_FILE: str = f"{FOLDER}/credentials.json"
# AI: Path to store the token after authorization
TOKEN_FILE: str = f"{FOLDER}/token.json"

# AI: Gmail API Scopes.
# AI: pubsub is for the watch command, gmail.readonly for reading messages.
# AI: If you need to modify emails (e.g., mark as read), add gmail.modify
SCOPES: List[str] = [
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/gmail.readonly",
]

# AI: Label to apply for the watch request (optional, but good practice)
WATCH_LABEL_IDS: List[str] = [
    "INBOX"
]  # AI: Only watch INBOX, or specify others e.g., ["IMPORTANT"]

# AI: --- Gmail API Authentication & Service ---


def get_gmail_service() -> Optional[Resource]:
    """AI: Authenticates with Gmail API and returns a service object."""
    creds: Optional[Credentials] = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"AI: Error loading token from {TOKEN_FILE}: {e}")
            creds = None  # AI: Ensure creds is None if loading fails

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("AI: Refreshing expired credentials...")
                creds.refresh(Request())
            except Exception as e:
                print(f"AI: Error refreshing credentials: {e}")
                creds = None  # AI: Could not refresh
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"AI: Error: Credentials file '{CREDENTIALS_FILE}' not found.")
                print(
                    "AI: Please download it from Google Cloud Console (OAuth 2.0 Client ID - Desktop app)."
                )
                return None
            try:
                print("AI: No valid credentials, initiating new OAuth flow...")
                flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES
                )
                # AI: Prefer local server for auth flow if possible
                # AI: Using a fixed port (e.g., 8080) for run_local_server
                # AI: Ensure http://localhost:8080/ is added to your OAuth Client ID's Authorized redirect URIs in Google Cloud Console.
                creds = flow.run_local_server(port=8080)  # AI: Changed from port=0
            except Exception as e:
                print(f"AI: Error during OAuth flow: {e}")
                return None

        if creds:
            try:
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
                print(f"AI: Credentials saved to {TOKEN_FILE}")
            except Exception as e:
                print(f"AI: Error saving token to {TOKEN_FILE}: {e}")
        else:
            print("AI: Failed to obtain credentials.")
            return None

    try:
        service: Resource = build("gmail", "v1", credentials=creds)
        print("AI: Gmail API service created successfully.")
        return service
    except Exception as e:
        print(f"AI: Error building Gmail service: {e}")
        return None


# AI: --- Gmail Watch Request ---


def start_gmail_watch(
    service: Resource, project_id: ProjectId, topic_name: TopicName
) -> bool:
    """AI: Initiates a watch on the user's Gmail account."""
    # AI: Full topic name for the watch request
    full_topic_name: str = f"projects/{project_id}/topics/{topic_name}"
    print(f"AI: Attempting to set up Gmail watch on topic: {full_topic_name}")

    # AI: Check current watch status first (optional, but can prevent errors)
    try:
        current_settings = (
            service.users().getProfile(userId="me", fields="historyId").execute()
        )
        print(
            f"AI: Current user profile fetched. History ID: {current_settings.get('historyId')}"
        )
    except Exception as e:
        print(f"AI: Could not fetch user profile (needed to check active watch): {e}")
        # AI: This isn't fatal for setting up a new watch, but good to know.

    # AI: Stop any existing watch (optional, but can be helpful if re-running)
    # AI: Be cautious with this in production if multiple services might be watching.
    # try:
    #     print("AI: Attempting to stop any existing watch...")
    #     service.users().stop(userId='me').execute()
    #     print("AI: Successfully stopped any existing watch.")
    # except Exception as e:
    #     print(f"AI: Info: Could not stop existing watch (may not be an issue): {e}")
    # AI: Ensure there is at least a pass or some statement in a try block if all actual code is commented out
    try:
        pass  # AI: Placeholder if the stop watch logic is commented out
    except Exception as e:
        print(
            f"AI: Info: Error during placeholder try for stop_watch (should be harmless if stop_watch is commented out): {e}"
        )

    request_body: Dict[str, Any] = {
        "labelIds": WATCH_LABEL_IDS,
        "topicName": full_topic_name,
        "labelFilterAction": "include",  # AI: Can be "include" or "exclude"
    }
    try:
        response: Dict[str, Any] = (
            service.users().watch(userId="me", body=request_body).execute()
        )
        print(f"AI: Gmail watch request successful. Response: {response}")
        # AI: A successful response includes 'historyId' and 'expiration'
        # AI: Expiration is in milliseconds since epoch. Watch lasts for 7 days typically.
        # AI: You should re-run this script or the watch command before it expires.
        if "expiration" in response:
            print(
                f"AI: Watch expires on: {time.ctime(int(response['expiration']) / 1000)}"
            )
        return True
    except Exception as e:
        print(f"AI: Error setting up Gmail watch: {e}")
        print("AI: Possible reasons:")
        print(
            "AI: 1. Pub/Sub topic does not exist or Gmail service account doesn't have publish permission."
        )
        print(
            f"AI:    Ensure topic 'projects/{project_id}/topics/{topic_name}' exists and permissions are set (see 1_setup.sh)."
        )
        print(
            "AI: 2. Invalid or insufficient OAuth scopes (ensure 'https://www.googleapis.com/auth/pubsub' is included)."
        )
        print(
            "AI: 3. The user has not granted the necessary permissions during OAuth flow."
        )
        return False


# AI: --- Pub/Sub Subscription & Message Handling ---


def process_email(message_id: str, service: Resource) -> None:
    """AI: Fetches and processes a single email."""
    try:
        # AI: Get the full email message
        msg: GmailMessage = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        if not msg:
            print(f"AI: Could not retrieve message {message_id}")
            return

        # AI: Extract headers to find the sender
        headers: List[Dict[str, str]] = msg.get("payload", {}).get("headers", [])
        sender_email: Optional[EmailAddress] = None
        subject: str = "No Subject"

        for header in headers:
            if header.get("name", "").lower() == "from":
                # AI: "From" header can be "Display Name <email@example.com>"
                # AI: We need to parse out the actual email
                from_header_value = header.get("value", "")
                if "<" in from_header_value and ">" in from_header_value:
                    start = from_header_value.rfind("<")
                    end = from_header_value.rfind(">")
                    if start != -1 and end != -1 and start < end:
                        sender_email = from_header_value[start + 1 : end]
                else:  # AI: If no <>, assume it's just the email (less common for "From")
                    sender_email = from_header_value
            elif header.get("name", "").lower() == "subject":
                subject = header.get("value", "No Subject")

        if sender_email:
            print(f"AI: Received email from: {sender_email}, Subject: '{subject}'")
            # AI: Convert to lower for case-insensitive comparison
            normalized_sender_email = sender_email.lower()
            normalized_target_emails = [target.lower() for target in TARGET_EMAIL_IDS]

            if normalized_sender_email in normalized_target_emails:
                print(
                    f"AI: ---> Email from '{sender_email}' matches a target email ID. Executing custom code..."
                )
                # AI: !!! YOUR CUSTOM CODE GOES HERE !!!
                # AI: You have access to the full \'msg\' object here, which is the GmailMessage dictionary.
                # AI: For example, to get the email body:
                # AI: payload = msg.get('payload')
                # AI: if payload:
                # AI:     parts = payload.get('parts')
                # AI:     body_data = ""
                # AI:     if parts: # AI: Multipart email
                # AI:         for part in parts:
                # AI:             if part.get('mimeType') == 'text/plain':
                # AI:                 body_data = part.get('body', {}).get('data')
                # AI:                 break
                # AI:             elif part.get('mimeType') == 'text/html': # AI: Fallback to HTML if no plain text
                # AI:                 body_data = part.get('body', {}).get('data')
                # AI:     else: # AI: Single part email
                # AI:         body_data = payload.get('body', {}).get('data')
                # AI:
                # AI:     if body_data:
                # AI:         decoded_body = base64.urlsafe_b64decode(body_data.encode('ASCII')).decode('utf-8')
                # AI:         print(f"AI: Email Body (first 100 chars): {decoded_body[:100]}...")
                # AI:     else:
                # AI:         print("AI: Email body not found or not in expected format.")

                print(f"AI: Custom action for {sender_email} would be triggered here.")
                # AI: Example: trigger_another_script(sender_email, subject, msg)

            else:
                print(
                    f"AI: Email from '{sender_email}' does not match any target email ID. Ignoring."
                )
        else:
            print(
                f"AI: Could not determine sender for message ID {message_id}. Headers: {headers}"
            )

    except Exception as e:
        print(f"AI: Error processing email (ID: {message_id}): {e}")
        import traceback

        traceback.print_exc()


def pubsub_callback(message: PubSubMessage) -> None:
    """AI: Callback function for Pub/Sub messages."""
    # AI: Corrected f-string by escaping the curly braces inside the string literal
    # AI: or by ensuring the expression part is valid.
    # AI: Original: print(f"\\\\nAI: Received Pub/Sub message: ID={message.message_id}, Data=\\\'{message.data}\\\'\")
    # AI: Corrected:
    print(
        f"\\nAI: Received Pub/Sub message: ID={message.message_id}, Data='{message.data}'"
    )
    try:
        # AI: The data is a JSON string like: {"emailAddress": "user@example.com", "historyId": "123456"}
        notification_data: Dict[str, Any] = json.loads(message.data.decode("utf-8"))
        email_address: EmailAddress = notification_data.get("emailAddress")
        history_id: str = notification_data.get("historyId")
        print(f"AI: Notification for email: {email_address}, History ID: {history_id}")

        # AI: Acknowledge the message early to prevent redelivery for processing errors
        # AI: If your processing is long, consider acknowledging after successful processing.
        message.ack()
        print(f"AI: Pub/Sub message {message.message_id} acknowledged.")

        # AI: Now use Gmail API to get changes since the last known historyId
        # AI: For simplicity, we'll just fetch the latest message if history_id is new.
        # AI: A more robust solution would use users.history.list to get all changes.
        # AI: For this demo, we assume the notification is for a new message and try to find it.

        gmail_service: Optional[Resource] = get_gmail_service()  # AI: Re-auth if needed
        if not gmail_service:
            print("AI: Failed to get Gmail service in callback. Cannot process email.")
            return

        # AI: List messages, the newest one should be related to the notification
        # AI: This is a simplification. A robust app would use historyId with messages.list or history.list.
        list_response = (
            gmail_service.users()
            .messages()
            .list(
                userId="me",
                labelIds=WATCH_LABEL_IDS,  # AI: e.g. ['INBOX']
                maxResults=1,  # AI: Get the most recent one
            )
            .execute()
        )

        messages: List[Dict[str, str]] = list_response.get("messages", [])
        if messages:
            latest_message_id: str = messages[0].get("id")
            if latest_message_id:
                print(
                    f"AI: Assuming latest message {latest_message_id} is related to notification."
                )
                process_email(latest_message_id, gmail_service)
            else:
                print("AI: No message ID found in the latest message listing.")
        else:
            print(
                "AI: No messages found after notification. This might be a non-message event (e.g., label change) or timing issue."
            )

    except json.JSONDecodeError as e:
        print(f"AI: Error decoding Pub/Sub message data: {e}")
        message.nack()  # AI: Not acknowledging if data is malformed
    except Exception as e:
        print(f"AI: Error in pubsub_callback: {e}")
        import traceback

        traceback.print_exc()
        message.nack()  # AI: Not acknowledging due to an unexpected error


def listen_for_messages(
    project_id: ProjectId,
    subscription_name: SubscriptionName,
    callback: Callable[[PubSubMessage], None],
) -> None:
    """AI: Listens for messages on a Pub/Sub subscription."""
    subscriber: pubsub_v1.SubscriberClient = pubsub_v1.SubscriberClient()
    # AI: Full subscription path
    subscription_path: str = subscriber.subscription_path(project_id, subscription_name)

    print(f"AI: Listening for messages on '{subscription_path}'...")
    print(f"AI: Will monitor emails from: {', '.join(TARGET_EMAIL_IDS)}")
    print("AI: Press Ctrl+C to exit.")

    # AI: The subscriber client is non-blocking, so we need to keep the main thread alive.
    # AI: `streaming_pull_future` is a future that will block until the stream is broken.
    streaming_pull_future: Any = subscriber.subscribe(
        subscription_path, callback=callback
    )

    try:
        # AI: Keep the main thread alive, waiting for messages indefinitely.
        # AI: You can add a timeout to `result()` if you want it to stop after a certain period.
        streaming_pull_future.result()
    except TimeoutError:  # AI: If streaming_pull_future.result(timeout=...) is used
        print("AI: Listening timeout reached. Shutting down...")
        streaming_pull_future.cancel()
        streaming_pull_future.result()  # AI: Ensure cleanup
    except KeyboardInterrupt:
        print("AI: Keyboard interrupt received. Shutting down gracefully...")
        streaming_pull_future.cancel()  # AI: Triggers the future to break.
        streaming_pull_future.result()  # AI: Wait for the cancellation to complete.
    except Exception as e:
        print(f"AI: An unexpected error occurred with the subscriber: {e}")
        streaming_pull_future.cancel()
        streaming_pull_future.result()
    finally:
        subscriber.close()
        print("AI: Pub/Sub subscriber closed.")


# AI: --- Main Execution ---

if __name__ == "__main__":
    print("AI: --- Gmail Pub/Sub Notification Demo ---")

    # AI: Validate configuration first
    if (
        "YOUR_PROJECT_ID" in GCP_PROJECT_ID
        or "YOUR_TOPIC_NAME" in PUB_SUB_TOPIC_NAME
        or "YOUR_SUBSCRIPTION_NAME" in PUB_SUB_SUBSCRIPTION_NAME
    ):
        print(
            "AI: CRITICAL ERROR: Please update GCP_PROJECT_ID, PUB_SUB_TOPIC_NAME, and PUB_SUB_SUBSCRIPTION_NAME in the script."
        )
        exit(1)

    if not TARGET_EMAIL_IDS or "specific.sender1@example.com" in TARGET_EMAIL_IDS:
        print(
            f"AI: WARNING: TARGET_EMAIL_IDS is {TARGET_EMAIL_IDS}. It is not configured or using default values. Please update it with the email addresses you want to monitor."
        )
        # AI: Decide if you want to exit or proceed with a warning
        # exit(1)

    # AI: 1. Get Gmail Service (handles OAuth)
    gmail_service_instance: Optional[Resource] = get_gmail_service()

    if gmail_service_instance:
        # AI: 2. Start Gmail Watch (if not already running or to refresh)
        # AI: You might not need to call this every time if a watch is already active and not expired.
        # AI: However, calling it ensures the watch is on the correct topic.
        # AI: The watch lasts for some days (typically 7), then needs to be renewed.
        if not start_gmail_watch(
            gmail_service_instance, GCP_PROJECT_ID, PUB_SUB_TOPIC_NAME
        ):
            print("AI: Failed to start or verify Gmail watch. Exiting.")
            print(
                "AI: Please check the output from 1_setup.sh and ensure Pub/Sub is correctly configured."
            )
            exit(
                1
            )  # AI: Exit if watch setup fails, as subscription won't receive anything.

        # AI: 3. Listen for Pub/Sub messages
        # AI: The callback function (pubsub_callback) will handle incoming messages.
        listen_for_messages(GCP_PROJECT_ID, PUB_SUB_SUBSCRIPTION_NAME, pubsub_callback)
    else:
        print("AI: Failed to authenticate and get Gmail service. Exiting.")

    print("AI: --- Script finished ---")

# This should activate a callback to send an email when an email is recieved
