from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic.base import RedirectView

from addresses import views


urlpatterns = [
    path('', RedirectView.as_view(pattern_name='chat_service', permanent=False)),
    path('health/', views.health, name='health'),
    path('chat_service/', views.chat_service, name='chat_service'),
    path('chat_test/', views.chat_test, name='chat_test'),
    path(
        'favicon.ico',
        RedirectView.as_view(url=staticfiles_storage.url('favicon.ico')),
    ),
]

if not settings.PUBLIC_CHATBOT_ONLY:
    urlpatterns += [
        path('addresses/', views.address_list, name='address_list'),
        path('addresses/<int:pk>/', views.address, name='address'),
        path('login/', views.login, name='login'),
        path('app_login/', views.app_login, name='app_login'),
        path('admin/', admin.site.urls),
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    ]
