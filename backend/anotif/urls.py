from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, NotifViewSet, PollViewSet

router = DefaultRouter()
router.register("Notif", NotifViewSet, basename="service-notification")
router.register("Comment", CommentViewSet, basename="service-notification-comment")
router.register("Poll", PollViewSet, basename="service-poll")

urlpatterns = [
    path("", include(router.urls)),
    path("admin/", admin.site.urls),
]
