from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

admin.site.site_header = 'SIGWeb — Cadastro de dados'
admin.site.site_title = 'SIGWeb'
admin.site.index_title = 'Dados do mapa'

urlpatterns = [
    path('admin/', admin.site.urls),
    # A raiz leva direto ao painel.
    path('', RedirectView.as_view(pattern_name='admin:index', permanent=False)),
]
