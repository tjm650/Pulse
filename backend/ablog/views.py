from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import CommunityDirectory, Notification
from api.permissions import IsOwnerOrReadOnly
from .models import Bloger as Blog
from .serializers import BlogSerializer


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all().select_related("sender", "service").prefetch_related(
        "tags", "interactions", "shared"
    )
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        service_id = request.data.get("service_id") or request.data.get("directoryId")
        description = request.data.get("description", "").strip()
        if not service_id or not description:
            return Response(
                {"detail": "service_id and description are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            service = CommunityDirectory.objects.get(pk=service_id, is_active=True)
        except CommunityDirectory.DoesNotExist:
            return Response({"detail": "Service directory not found."}, status=status.HTTP_404_NOT_FOUND)

        can_publish = (
            service.creator_id == request.user.pk
            or service.moderators.filter(pk=request.user.pk).exists()
        )
        if not can_publish:
            return Response(
                {"detail": "Only the service owner or an approved moderator can publish here."},
                status=status.HTTP_403_FORBIDDEN,
            )

        blog = Blog.objects.create(
            sender=request.user,
            service=service,
            description=description,
            image=request.FILES.get("image"),
        )
        raw_tags = request.data.getlist("tags") if hasattr(request.data, "getlist") else request.data.get("tags", [])
        if isinstance(raw_tags, str):
            raw_tags = [value.strip() for value in raw_tags.split(",") if value.strip()]
        tag_ids = []
        for value in raw_tags or []:
            try:
                tag_ids.append(int(value))
            except (TypeError, ValueError):
                continue
        if tag_ids:
            from api.models import User
            blog.tags.set(User.objects.filter(pk__in=tag_ids, is_active=True))

        return Response(self.get_serializer(blog).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="interact")
    def interact(self, request, pk=None):
        blog = self.get_object()
        interacted = blog.interactions.filter(pk=request.user.pk).exists()
        if interacted:
            blog.interactions.remove(request.user)
        else:
            blog.interactions.add(request.user)
        return Response({
            "interacted": not interacted,
            "interactions_count": blog.interactions.count(),
        })

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        blog = self.get_object()
        shared = blog.shared.filter(pk=request.user.pk).exists()
        if shared:
            blog.shared.remove(request.user)
        else:
            blog.shared.add(request.user)
        return Response({
            "shared": not shared,
            "shares_count": blog.shared.count(),
        })
