"""
URL configuration for kids_App project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# kids_App/urls.py
import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

admin.site.site_header = "Kids_app"
admin.site.index_title = "Admin"

urlpatterns = [
    path("admin/", admin.site.urls),
    # API apps
    path("", include("playground.urls")),
    path("api/profiles/", include("profiles.urls")),
    path("api/lessons/", include("lessons.urls")),
    path("api/quizzes/", include("quizzes.urls")),
    path("api/progress/", include("progress.urls")),
    path("api/ai/", include("ai.urls")),  # Note the trailing slash
    path("api/ml_online/", include("ml_online.urls")),
    path("api/ml_offline/", include("ml_offline.urls")),
    path("api/core/", include("core.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
