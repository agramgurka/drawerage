import re

from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path('', include('application.urls')),
    path('admin/', admin.site.urls),
]
if settings.SERVE_STATIC_WITH_DJANGO:
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
            serve,
            kwargs=dict(document_root=settings.MEDIA_ROOT)
        ),
    ]
    urlpatterns += [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(settings.STATIC_URL.lstrip("/")),
            serve,
            kwargs=dict(document_root=settings.STATIC_ROOT)
        ),
    ]
