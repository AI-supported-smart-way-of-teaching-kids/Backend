from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentRealtimeAggregateViewSet

router = DefaultRouter()
router.register(r"aggregates", StudentRealtimeAggregateViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
