"""Script for testing email notification configuration.

Generates a test notification and dispatches it via the email backend. Can be used in
deployment to test configuration is correct.
"""

import argparse

from invenio_accounts.proxies import current_datastore
from invenio_app.factory import create_app
from invenio_notifications.models import Notification, Recipient
from invenio_notifications.tasks import dispatch_notification


def send_test_notification(user_email):
    """Send email with invenio_notifications.tasks.dispatch_notification."""
    if not (user := current_datastore.find_user(email=user_email)):
        raise ValueError(f"User with email {user_email} not found.")

    recipient = Recipient(data={"id": str(user.id), "email": user.email})
    notification = Notification(
        type="test_notification",
        context={
            "message": "This is a test notification from the script.",
        },
    )

    dispatch_notification(
        backend="email", recipient=recipient.dumps(), notification=notification.dumps()
    )
    print(f"Notification sent to {user.email} (user id: {user.id})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send a test notification to a user by email."
    )
    parser.add_argument("user_email", help="The email address of the user to notify.")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        send_test_notification(args.user_email)
