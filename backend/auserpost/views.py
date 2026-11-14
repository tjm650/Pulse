from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.models import Notification
from api.permissions import IsOwnerOrReadOnly
from .models import Comment, Post
from .serializers import CommentSerializer, PostSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().select_related("sender").prefetch_related(
        "likes", "interactions", "comments"
    )
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user)
        return Response(
            {"message": "Post Created Successfully", "post": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="like")
    def like(self, request, pk=None):
        post = self.get_object()
        already_liked = post.likes.filter(pk=request.user.pk).exists()
        if already_liked:
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)
            if post.sender_id != request.user.pk:
                Notification.objects.create(
                    recipient_id=post.sender_id,
                    sender=request.user,
                    notification_type="like",
                    title="New post like",
                    message=f"{request.user.username} liked your post.",
                    related_post_id=post.pk,
                    data={"post_id": post.pk},
                )
        return Response({
            "liked": not already_liked,
            "likes_count": post.likes.count(),
        })

    @action(detail=True, methods=["post"], url_path="interact")
    def interact(self, request, pk=None):
        post = self.get_object()
        interacted = post.interactions.filter(pk=request.user.pk).exists()
        if interacted:
            post.interactions.remove(request.user)
        else:
            post.interactions.add(request.user)
        return Response({
            "interacted": not interacted,
            "interactions_count": post.interactions.count(),
        })


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related("sender", "post").prefetch_related(
        "likes", "interactions"
    )
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        post_id = self.request.query_params.get("post")
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset.order_by("-created")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.request.data.get("post"))
        serializer.save(sender=self.request.user, post=post)
        if post.sender_id != self.request.user.pk:
            Notification.objects.create(
                recipient_id=post.sender_id,
                sender=self.request.user,
                notification_type="comment",
                title="New post comment",
                message=f"{self.request.user.username} commented on your post.",
                related_post_id=post.pk,
                related_comment_id=serializer.instance.pk,
                data={"post_id": post.pk, "comment_id": serializer.instance.pk},
            )

    @action(detail=True, methods=["post"], url_path="like")
    def like(self, request, pk=None):
        comment = self.get_object()
        already_liked = comment.likes.filter(pk=request.user.pk).exists()
        if already_liked:
            comment.likes.remove(request.user)
        else:
            comment.likes.add(request.user)
        return Response({
            "liked": not already_liked,
            "likes_count": comment.likes.count(),
        })

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
