"""Authenticated, participant-scoped WebSocket handlers for direct and group chat."""
import base64
import binascii
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import time

from afollows.models import Connection
from amessages.models import Message
from amessages.serializers import MessageSerializer
from api.models import User, UserPreference
from api.serializers import PublicUserSerializer
from community.models import GroupChat, GroupCon


class SecureChatConsumer(WebsocketConsumer):
    """Only exposes the chat operations that have explicit object-level checks.

    The legacy consumer remains in the repository for reference but is no longer
    routed. Other legacy event sources are rejected until individually reviewed.
    """

    MAX_TEXT_LENGTH = 10000
    MAX_IMAGE_BYTES = 5 * 1024 * 1024
    PAGE_SIZE = 15

    def connect(self):
        self.user = self.scope.get("user")
        self.auth_exp = self.scope.get("auth_exp")
        if not self.user or not self.user.is_authenticated:
            self.close(code=4401)
            return
        self.group_name = f"pulse_user_{self.user.pk.hex}"
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        if getattr(self, "group_name", None):
            async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def send_group(self, user, source, data):
        """Send a response/event to a user's private socket group."""
        user_id = user.pk if isinstance(user, User) else user
        group_name = f"pulse_user_{str(user_id).replace('-', '')}"
        async_to_sync(self.channel_layer.group_send)(
            group_name,
            {"type": "socket.event", "source": source, "data": data},
        )

    def socket_event(self, event):
        self.send(text_data=json.dumps({
            "source": event["source"],
            "data": event["data"],
        }, default=str))

    def _error(self, code, detail):
        self.send(text_data=json.dumps({
            "source": "error",
            "data": {"code": code, "detail": detail},
        }))

    def receive(self, text_data=None, bytes_data=None):
        if self.auth_exp is None or time.time() >= float(self.auth_exp):
            self.close(code=4401)
            return
        if not text_data:
            self._error("invalid_payload", "A JSON text payload is required.")
            return
        try:
            data = json.loads(text_data)
        except (TypeError, ValueError):
            self._error("invalid_json", "The payload must be valid JSON.")
            return
        if not isinstance(data, dict):
            self._error("invalid_payload", "The payload must be a JSON object.")
            return

        source = data.get("source")
        handlers = {
            "message.list": self.message_list,
            "message.send": self.message_send,
            "message.type": self.message_type,
            "message.red": self.message_mark_read,
            "groupmessages.send": self.group_message_send,
            "groupmessages.list": self.group_message_list,
            "group_connect.list": self.group_connection_list,
        }
        handler = handlers.get(source)
        if handler is None:
            self._error(
                "event_not_enabled",
                "This WebSocket event is not enabled on the secured chat endpoint yet.",
            )
            return
        try:
            handler(data)
        except (Connection.DoesNotExist, GroupCon.DoesNotExist):
            self._error("not_found", "The requested conversation was not found.")
        except PermissionError:
            self._error("forbidden", "You are not a participant in this conversation.")
        except (TypeError, ValueError, KeyError):
            self._error("invalid_payload", "One or more event fields are invalid.")

    def _direct_connection(self, raw_id):
        if raw_id is None:
            raise ValueError("connectionId is required")
        connection = Connection.objects.get(pk=raw_id, accepted=True)
        if self.user.pk not in (connection.sender_id, connection.receiver_id):
            raise PermissionError("Not a participant")
        return connection

    def _group_connection(self, raw_id):
        if raw_id is None:
            raise ValueError("grpConnId is required")
        connection = GroupCon.objects.get(pk=raw_id)
        if not (
            connection.users.filter(pk=self.user.pk).exists()
            or connection.creator_id == self.user.pk
        ):
            raise PermissionError("Not a group member")
        return connection

    def message_list(self, data):
        connection = self._direct_connection(data.get("connectionId"))
        try:
            page = max(0, min(int(data.get("page", 0)), 100000))
        except (TypeError, ValueError):
            raise ValueError("page must be an integer")
        qs = Message.objects.filter(connection=connection).select_related("sender").order_by("-created")
        total = qs.count()
        messages = qs[page * self.PAGE_SIZE:(page + 1) * self.PAGE_SIZE]
        recipient = connection.receiver if connection.sender_id == self.user.pk else connection.sender
        payload = {
            "messages": MessageSerializer(messages, context={"user": self.user}, many=True).data,
            "next": page + 1 if total > (page + 1) * self.PAGE_SIZE else None,
            "connect": PublicUserSerializer(recipient).data,
        }
        self.send_group(self.user, "message.list", payload)

    def message_send(self, data):
        connection = self._direct_connection(data.get("connectionId"))
        message_text = data.get("message") or ""
        if not isinstance(message_text, str) or len(message_text) > self.MAX_TEXT_LENGTH:
            raise ValueError("message must be text of at most 10000 characters")

        image = None
        image_data = data.get("imageBase64")
        if image_data:
            if not isinstance(image_data, str):
                raise ValueError("imageBase64 must be a base64 string")
            try:
                decoded = base64.b64decode(image_data, validate=True)
            except (binascii.Error, ValueError):
                raise ValueError("imageBase64 is invalid")
            if len(decoded) > self.MAX_IMAGE_BYTES:
                raise ValueError("Image exceeds the 5 MB limit")
            filename = data.get("imageFilename")
            if not isinstance(filename, str) or not filename.strip() or len(filename) > 150:
                raise ValueError("A valid imageFilename is required")
            from django.core.files.base import ContentFile
            image = ContentFile(decoded, name=filename)

        if not message_text.strip() and image is None:
            raise ValueError("A message or image is required")

        recipient = connection.receiver if connection.sender_id == self.user.pk else connection.sender
        try:
            recipient_preferences = UserPreference.objects.get(user=recipient)
        except UserPreference.DoesNotExist:
            recipient_preferences = None
        if recipient_preferences and recipient_preferences.allow_messages_from == "none":
            raise PermissionError("Recipient does not accept messages")
        with transaction.atomic():
            message = Message.objects.create(
                connection=connection,
                sender=self.user,
                image=image,
                description=message_text,
            )
        sender_payload = {
            "message": MessageSerializer(message, context={"user": self.user}).data,
            "connect": PublicUserSerializer(recipient).data,
        }
        recipient_payload = {
            "message": MessageSerializer(message, context={"user": recipient}).data,
            "connect": PublicUserSerializer(self.user).data,
        }
        self.send_group(self.user, "message.send", sender_payload)
        self.send_group(recipient, "message.send", recipient_payload)

    def message_type(self, data):
        connection = self._direct_connection(data.get("connectionId"))
        recipient = connection.receiver if connection.sender_id == self.user.pk else connection.sender
        self.send_group(recipient, "message.type", {"username": self.user.username})

    def message_mark_read(self, data):
        connection = self._direct_connection(data.get("connectionId"))
        updated = Message.objects.filter(
            connection=connection, red=False
        ).exclude(sender=self.user).update(red=True)
        self.send_group(self.user, "message.red", {
            "connectionId": connection.pk,
            "updated": updated,
            "action": data.get("action"),
        })
        other = connection.receiver if connection.sender_id == self.user.pk else connection.sender
        self.send_group(other, "message.red", {
            "connectionId": connection.pk,
            "updated": updated,
            "action": data.get("action"),
        })

    def _group_message_data(self, message, viewer=None):
        viewer = viewer or self.user
        return {
            "id": message.pk,
            "is_me": message.sender_id == viewer.pk,
            "sender": PublicUserSerializer(message.sender).data,
            "text": message.text,
            "created": message.created.isoformat(),
        }

    def group_message_send(self, data):
        connection = self._group_connection(data.get("grpConnId"))
        message_text = data.get("grpmessage") or ""
        if not isinstance(message_text, str) or not message_text.strip() or len(message_text) > self.MAX_TEXT_LENGTH:
            raise ValueError("grpmessage must contain 1-10000 characters")
        with transaction.atomic():
            message = GroupChat.objects.create(
                connection=connection,
                sender=self.user,
                text=message_text,
            )
            connection.updated = timezone.now()
            connection.save(update_fields=["updated"])

        members = list(connection.users.all())
        if connection.creator_id not in {member.pk for member in members}:
            members.append(connection.creator)
        for member in members:
            payload = {
                "grpmessage": self._group_message_data(message, member),
                "grpconnect": PublicUserSerializer(self.user).data,
            }
            self.send_group(member, "groupmessages.send", payload)

    def group_message_list(self, data):
        connection = self._group_connection(data.get("grpConnId"))
        try:
            page = max(0, min(int(data.get("page", 0)), 100000))
        except (TypeError, ValueError):
            raise ValueError("page must be an integer")
        qs = GroupChat.objects.filter(connection=connection).select_related("sender").order_by("-created")
        messages = qs[page * self.PAGE_SIZE:(page + 1) * self.PAGE_SIZE]
        members = list(connection.users.all())
        if connection.creator_id not in {member.pk for member in members}:
            members.append(connection.creator)
        payload = {
            "grp_messages": [self._group_message_data(message) for message in messages],
            "grpconnect": PublicUserSerializer(members, many=True).data,
        }
        self.send_group(self.user, "groupmessages.list", payload)

    def group_connection_list(self, data):
        connections = GroupCon.objects.filter(
            Q(users=self.user) | Q(creator=self.user)
        ).distinct().order_by("-updated")
        payload = []
        for connection in connections:
            latest = connection.group_chats.select_related("sender").order_by("-created").first()
            members = list(connection.users.all())
            if connection.creator_id not in {member.pk for member in members}:
                members.append(connection.creator)
            payload.append({
                "id": connection.pk,
                "name": connection.name,
                "group_chats_sender": PublicUserSerializer(latest.sender).data if latest else None,
                "group_connect": PublicUserSerializer(self.user).data,
                "members": PublicUserSerializer(members, many=True).data,
                "preview": latest.text if latest else "You have a new connect",
                "updated": (latest.created if latest else connection.updated).isoformat(),
            })
        self.send_group(self.user, "group_connect.list", payload)
