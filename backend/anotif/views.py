from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
import json
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import CommunityDirectory
from api.permissions import IsOwnerOrReadOnly
from .models import Comment, Notif, Poll
from .serializers import CommentSerializer, NotifSerializer, PollSerializer


class NotifViewSet(viewsets.ModelViewSet):
    serializer_class = NotifSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        user = self.request.user
        queryset = Notif.objects.select_related("sender", "service").prefetch_related(
            "likes", "interactions", "notif_comments"
        ).filter(
            Q(service__public=True)
            | Q(service__followers=user)
            | Q(service__creator=user)
            | Q(service__moderators=user)
        ).filter(service__is_active=True).distinct().order_by("-created")
        service_id = self.request.query_params.get("service")
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def get_permissions(self):
        if getattr(self, "action", None) in {"like", "interact"}:
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        service_id = request.data.get("service") or request.data.get("service_id")
        service = get_object_or_404(CommunityDirectory, pk=service_id, is_active=True)
        can_publish = (
            service.creator_id == request.user.pk
            or service.moderators.filter(pk=request.user.pk).exists()
        )
        if not can_publish:
            return Response(
                {"detail": "Only the service owner or an approved moderator can publish updates."},
                status=status.HTTP_403_FORBIDDEN,
            )
        extra_data = request.data.get("extra_data") or {}
        if isinstance(extra_data, str):
            try:
                extra_data = json.loads(extra_data)
            except json.JSONDecodeError:
                return Response({"detail": "extra_data must be valid JSON."}, status=400)
        if not isinstance(extra_data, dict):
            return Response({"detail": "extra_data must be a JSON object."}, status=400)

        update_type = request.data.get("update_type", "Update")
        with transaction.atomic():
            notif = Notif.objects.create(
                sender=request.user,
                service=service,
                update_type=update_type,
                description=request.data.get("description", ""),
                image=request.FILES.get("image"),
                extra_data=extra_data,
            )
            poll_data = extra_data.get("poll") if isinstance(extra_data.get("poll"), dict) else extra_data
            if str(update_type).lower() == "poll":
                title = poll_data.get("title") or "Community Poll"
                question = poll_data.get("poll_question") or poll_data.get("description") or request.data.get("description", "")
                sections = poll_data.get("poll_sections") or []
                if not question or not sections:
                    return Response(
                        {"detail": "Polls require a question and at least one poll section."},
                        status=400,
                    )
                Poll.objects.create(
                    notification=notif,
                    title=title,
                    poll_question=question,
                    poll_type=poll_data.get("poll_type", "single"),
                    category=poll_data.get("category", "general"),
                    visibility=poll_data.get("visibility", "public"),
                    poll_sections=sections,
                    images=poll_data.get("images") or [],
                    settings=poll_data.get("settings") or {},
                    duration_hours=int(poll_data.get("duration_hours") or 24),
                    allow_comments=bool(poll_data.get("allow_comments", True)),
                    allow_multiple_votes=bool(poll_data.get("allow_multiple_votes", False)),
                    anonymous_voting=bool(poll_data.get("anonymous_voting", False)),
                    hide_results_until_expired=bool(poll_data.get("hide_results_until_expired", False)),
                    show_results_after_vote=bool(poll_data.get("show_results_after_vote", True)),
                    send_reminders=bool(poll_data.get("send_reminders", True)),
                    reminder_frequency_hours=int(poll_data.get("reminder_frequency_hours") or 12),
                    tags=poll_data.get("tags") or [],
                )

        response_data = self.get_serializer(notif).data
        if str(update_type).lower() == "poll":
            poll = Poll.objects.get(notification=notif)
            response_data["poll"] = PollSerializer(poll, context=self.get_serializer_context()).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="like")
    def like(self, request, pk=None):
        notif = self.get_object()
        liked = notif.likes.filter(pk=request.user.pk).exists()
        if liked:
            notif.likes.remove(request.user)
        else:
            notif.likes.add(request.user)
        return Response({"liked": not liked, "likes_count": notif.likes.count()})

    @action(detail=True, methods=["post"], url_path="interact")
    def interact(self, request, pk=None):
        notif = self.get_object()
        interacted = notif.interactions.filter(pk=request.user.pk).exists()
        if interacted:
            notif.interactions.remove(request.user)
        else:
            notif.interactions.add(request.user)
        return Response({
            "interacted": not interacted,
            "interactions_count": notif.interactions.count(),
        })


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related("sender", "post").prefetch_related(
        "likes", "interactions"
    )
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (JSONParser,)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset().filter(
            Q(post__service__public=True)
            | Q(post__service__creator=user)
            | Q(post__service__followers=user)
            | Q(post__service__moderators=user)
        ).filter(post__service__is_active=True).distinct()
        post_id = self.request.query_params.get("post")
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset.order_by("-created")

    def get_permissions(self):
        if getattr(self, "action", None) in {"like", "interact"}:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def perform_create(self, serializer):
        notif = get_object_or_404(Notif, pk=self.request.data.get("post"))
        if not self._can_view_notification(notif):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You cannot comment on this service update.")
        serializer.save(sender=self.request.user, post=notif)

    def _can_view_notification(self, notif):
        service = notif.service
        user = self.request.user
        return (
            service.public
            or service.creator_id == user.pk
            or service.moderators.filter(pk=user.pk).exists()
            or service.followers.filter(pk=user.pk).exists()
        )

    @action(detail=True, methods=["post"], url_path="like")
    def like(self, request, pk=None):
        comment = self.get_object()
        liked = comment.likes.filter(pk=request.user.pk).exists()
        if liked:
            comment.likes.remove(request.user)
        else:
            comment.likes.add(request.user)
        return Response({"liked": not liked, "likes_count": comment.likes.count()})

    @action(detail=True, methods=["post"], url_path="interact")
    def interact(self, request, pk=None):
        comment = self.get_object()
        interacted = comment.interactions.filter(pk=request.user.pk).exists()
        if interacted:
            comment.interactions.remove(request.user)
        else:
            comment.interactions.add(request.user)
        return Response({
            "interacted": not interacted,
            "interactions_count": comment.interactions.count(),
        })


class PollViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PollSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Poll.objects.select_related(
            "notification", "notification__service", "notification__sender"
        ).filter(
            notification__service__is_active=True
        ).filter(
            Q(visibility="public", notification__service__public=True)
            | Q(visibility="public", notification__service__creator=user)
            | Q(visibility="public", notification__service__followers=user)
            | Q(visibility="followers", notification__service__followers=user)
            | Q(visibility="private", notification__sender=user)
            | Q(notification__service__creator=user)
            | Q(notification__service__moderators=user)
        ).distinct().order_by("-created_at")

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        poll_status = self.request.query_params.get("status", "active")
        if poll_status == "active":
            queryset = queryset.filter(is_active=True, expired=False)
        elif poll_status == "expired":
            queryset = queryset.filter(expired=True)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    @action(detail=True, methods=["post"], url_path="vote")
    def vote(self, request, pk=None):
        indices = request.data.get("pollOptionIndices", request.data.get("option_indices", []))
        if not isinstance(indices, list) or not all(isinstance(value, int) and value >= 0 for value in indices):
            return Response({"detail": "pollOptionIndices must be a list of non-negative integers."}, status=400)
        try:
            with transaction.atomic():
                poll = self.get_queryset().select_for_update().get(pk=pk)
                poll.record_vote(request.user, indices)
        except Poll.DoesNotExist:
            return Response({"detail": "Poll not found."}, status=404)
        except ValueError as error:
            return Response({"detail": str(error)}, status=400)
        poll.refresh_from_db()
        return Response(self.get_serializer(poll).data)

    @action(detail=True, methods=["get"], url_path="statistics")
    def statistics(self, request, pk=None):
        poll = self.get_object()
        results = poll.get_poll_results()
        return Response({
            "statistics": results.get("statistics", {}),
            "vote_distribution": results.get("vote_distribution", []),
            "winners": results.get("winners", []),
        })
