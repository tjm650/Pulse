from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AppFeedbackViewSet, AppNotifViewSet, AppReportViewSet

router = DefaultRouter()
router.register("Notif", AppNotifViewSet, basename="app-notification")
router.register("Report", AppReportViewSet, basename="app-report")
router.register("Feedback", AppFeedbackViewSet, basename="app-feedback")

urlpatterns = [
    path("", include(router.urls)),
    path("admin/", admin.site.urls),
]
