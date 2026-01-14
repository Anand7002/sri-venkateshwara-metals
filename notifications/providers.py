import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMessage

try:
    from twilio.base.exceptions import TwilioRestException
    from twilio.rest import Client
except ImportError:  # pragma: no cover - optional dependency
    TwilioRestException = Exception
    Client = None


logger = logging.getLogger(__name__)


class NotificationSendError(Exception):
    """Raised when a provider fails to deliver a message."""


@dataclass
class BaseChannelProvider:
    channel: str
    config: dict

    def send(self, recipient: str, subject: str, message: str, attachments=None):
        raise NotImplementedError


class EmailProvider(BaseChannelProvider):
    def send(self, recipient: str, subject: str, message: str, attachments=None):
        from_email = self.config.get('from_email') or settings.DEFAULT_FROM_EMAIL
        try:
            email = EmailMessage(
                subject=subject or '',
                body=message,
                from_email=from_email,
                to=[recipient],
            )
            if attachments:
                for attachment in attachments:
                    email.attach(
                        attachment['filename'],
                        attachment['content'],
                        attachment.get('mimetype', 'application/octet-stream'),
                    )
            email.send(fail_silently=False)
        except Exception as exc:  # pragma: no cover - depends on backend
            raise NotificationSendError(str(exc)) from exc


class TwilioProvider(BaseChannelProvider):
    _client: Optional[Client] = None

    def _ensure_client(self):
        if self._client:
            return self._client
        creds = settings.NOTIFICATIONS.get('TWILIO', {})
        account_sid = creds.get('ACCOUNT_SID')
        auth_token = creds.get('AUTH_TOKEN')
        if not all([Client, account_sid, auth_token]):
            raise NotificationSendError('Twilio credentials are not configured.')
        self._client = Client(account_sid, auth_token)
        return self._client

    def _format_address(self, recipient: str) -> tuple[str, str]:
        from_number = self.config.get('from_number')
        if not from_number:
            raise NotificationSendError(f'Missing from number for {self.channel} channel.')
        if self.channel == 'whatsapp':
            from_number = from_number if from_number.startswith('whatsapp:') else f'whatsapp:{from_number}'
            to_number = recipient if recipient.startswith('whatsapp:') else f'whatsapp:{recipient}'
        else:
            to_number = recipient
        return from_number, to_number

    def send(self, recipient: str, subject: str, message: str, attachments=None):
        client = self._ensure_client()
        from_number, to_number = self._format_address(recipient)
        body = message
        try:
            client.messages.create(body=body, from_=from_number, to=to_number)
        except TwilioRestException as exc:  # pragma: no cover - external API
            raise NotificationSendError(str(exc)) from exc


class ConsoleProvider(BaseChannelProvider):
    """Fallback provider that just logs the notification."""

    def send(self, recipient: str, subject: str, message: str, attachments=None):
        logger.info(
            'Console notification (%s) → %s\n%s\nAttachments: %s',
            self.channel,
            recipient,
            message,
            bool(attachments),
        )

