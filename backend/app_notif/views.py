from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from api.models import CommunityDirectory
from .models import AppNotif, AppReport, AppFeedback
from .serializers import AppNotifSerializer, AppReportSerializer, AppFeedbackSerializer


class AppNotifViewSet(viewsets.ModelViewSet):
    serializer_class = AppNotifSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return AppNotif.objects.filter(receiver=self.request.user).select_related(
            "sender", "sender_user"
        ).prefetch_related("receiver", "interactions").order_by("-created")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        service_id = request.data.get("directoryId") or request.data.get("service_id")
        service = get_object_or_404(CommunityDirectory, pk=service_id, is_active=True)
        can_publish = (
            service.creator_id == request.user.pk
            or service.moderators.filter(pk=request.user.pk).exists()
        )
        if not can_publish:
            return Response({"detail": "Only service owners and moderators can send app notifications."}, status=403)

        receiver_id = request.data.get("ReceiverId") or request.data.get("receiver_id")
        recipients = service.followers.all()
        if receiver_id:
            recipients = recipients.filter(pk=receiver_id)
            if not recipients.exists():
                return Response({"detail": "The recipient must follow this service."}, status=403)

        notification = AppNotif.objects.create(
            sender=service,
            sender_user=request.user,
            subject=request.data.get("subject", ""),
            description=request.data.get("description", ""),
            image=request.FILES.get("image"),
        )
        notification.receiver.set(recipients)
        return Response(self.get_serializer(notification).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="interact")
    def interact(self, request, pk=None):
        notification = self.get_object()
        already_interacted = notification.interactions.filter(pk=request.user.pk).exists()
        if already_interacted:
            notification.interactions.remove(request.user)
        else:
            notification.interactions.add(request.user)
        return Response({
            "interacted": not already_interacted,
            "interactions_count": notification.interactions.count(),
        })


class AppReportViewSet(viewsets.ModelViewSet):
    serializer_class = AppReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return AppReport.objects.filter(sender=self.request.user).prefetch_related(
            "attendand", "red_by"
        ).order_by("-created")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        report = AppReport.objects.create(
            sender=request.user,
            subject=request.data.get("subject", ""),
            description=request.data.get("description", ""),
            image=request.FILES.get("image"),
        )
        return Response(self.get_serializer(report).data, status=status.HTTP_201_CREATED)


class AppFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = AppFeedbackSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return AppFeedback.objects.filter(sender=self.request.user).prefetch_related(
            "attendand", "red_by"
        ).order_by("-created")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        feedback = AppFeedback.objects.create(
            sender=request.user,
            description=request.data.get("description", ""),
            image=request.FILES.get("image"),
        )
        return Response(self.get_serializer(feedback).data, status=status.HTTP_201_CREATED)
