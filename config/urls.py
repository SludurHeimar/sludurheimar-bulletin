"""
URL configuration for config project.

Admin and the language-switch endpoint stay unprefixed; everything the
public sees is wrapped in i18n_patterns so it gets /en/... or /is/...
automatically based on the visitor's chosen language.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

from board.views import switch_language

urlpatterns = [
    path('admin/', admin.site.urls),
    # Our own view (see board/views.py) - Django's built-in set_language
    # view doesn't reliably swap the URL prefix from this unprefixed path.
    path('i18n/setlang/', switch_language, name='set_language'),
]

urlpatterns += i18n_patterns(
    path('', include('board.urls')),
    prefix_default_language=True,
)
