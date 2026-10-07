from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import AcaoParceiro, ColetaProducao, Comunidade, LocalParceiro, Parceiro


VAZIO = format_html('<span style="opacity:.5">—</span>')


# ---------- Forms ----------

class ColetaProducaoForm(forms.ModelForm):
    """Impede números que não fecham com o total de produtores."""

    class Meta:
        model = ColetaProducao
        fields = '__all__'

    GRUPOS = (
        (_("sistemas de criação"), ['criacao_extensiva', 'criacao_semi_extensiva', 'criacao_intensiva']),
        (_("escrituração zootécnica"), ['escrituracao_sim', 'escrituracao_nao']),
    )

    def clean(self):
        dados = super().clean()
        total = dados.get('total_produtores')
        if total is None:
            return dados

        for rotulo, campos in self.GRUPOS:
            soma = sum(dados.get(campo) or 0 for campo in campos)
            if soma > total:
                self.add_error(None, forms.ValidationError(
                    _("A soma de %(grupo)s (%(soma)s) é maior que o total de "
                      "produtores (%(total)s)."),
                    params={'grupo': rotulo, 'soma': soma, 'total': total},
                ))
        return dados


# ---------- Inlines ----------

class ColetaProducaoInline(admin.StackedInline):
    model = ColetaProducao
    form = ColetaProducaoForm
    extra = 0
    ordering = ['-data_coleta', '-id']
    fieldsets = (
        (None, {
            'fields': ('data_coleta', 'total_produtores', ('qtd_caprinos', 'qtd_ovinos')),
        }),
        (_("Sistemas de criação"), {
            'fields': (('criacao_extensiva', 'criacao_semi_extensiva', 'criacao_intensiva'),),
        }),
        (_("Escrituração zootécnica"), {
            'fields': (('escrituracao_sim', 'escrituracao_nao'),),
        }),
        (_("Nota técnica de campo"), {
            'fields': ('observacoes',),
        }),
    )
    # O Django não aninha inlines: as ações de parceiros ficam na página da
    # coleta, e este link leva até ela.
    show_change_link = True


class AcaoParceiroInline(admin.StackedInline):
    # Empilhado, não em tabela: na tabela os ícones do campo Parceiro empurravam
    # a coluna da descrição para fora da área visível do formulário.
    model = AcaoParceiro
    extra = 0
    fields = ('data_acao', 'parceiro', 'descricao')
    autocomplete_fields = ['parceiro']
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 4, 'style': 'width: 100%'})},
    }


class LocalParceiroInline(admin.TabularInline):
    model = LocalParceiro
    extra = 0
    fields = ('nome', 'endereco', 'latitude', 'longitude')


# ---------- ModelAdmins ----------

@admin.register(Comunidade)
class ComunidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'municipio', 'coordenadas', 'coleta_em', 'produtores', 'caprinos', 'ovinos')
    list_filter = ('municipio',)
    search_fields = ('nome', 'municipio', 'informacoes_adicionais')
    inlines = [ColetaProducaoInline]
    fieldsets = (
        (None, {
            'fields': ('nome', 'municipio', 'informacoes_adicionais'),
        }),
        (_("Localização"), {
            'fields': (('latitude', 'longitude'),),
            'description': _(
                "Coordenadas em graus decimais (WGS 84). No Semiárido, latitude "
                "fica por volta de -9 e longitude de -40. O ponto no mapa é "
                "calculado pelo banco a partir desses dois valores."
            ),
        }),
    )

    def get_queryset(self, request):
        # A listagem mostra dados da última coleta: sem o prefetch seria uma
        # query por comunidade.
        return super().get_queryset(request).prefetch_related('coletas')

    @admin.display(description=_("Coordenadas"))
    def coordenadas(self, obj):
        if obj.latitude is None or obj.longitude is None:
            return VAZIO
        return f"{obj.latitude:.4f}, {obj.longitude:.4f}"

    @admin.display(description=_("Última coleta"))
    def coleta_em(self, obj):
        coleta = obj.ultima_coleta
        if coleta is None:
            return format_html('<span style="opacity:.5">{}</span>', _("sem coleta"))
        return coleta.data_coleta

    @admin.display(description=_("Produtores"))
    def produtores(self, obj):
        coleta = obj.ultima_coleta
        return coleta.total_produtores if coleta else VAZIO

    @admin.display(description=_("Caprinos"))
    def caprinos(self, obj):
        coleta = obj.ultima_coleta
        return coleta.qtd_caprinos if coleta else VAZIO

    @admin.display(description=_("Ovinos"))
    def ovinos(self, obj):
        coleta = obj.ultima_coleta
        return coleta.qtd_ovinos if coleta else VAZIO


@admin.register(ColetaProducao)
class ColetaProducaoAdmin(admin.ModelAdmin):
    form = ColetaProducaoForm
    list_display = (
        'comunidade', 'data_coleta', 'total_produtores',
        'qtd_caprinos', 'qtd_ovinos', 'escrituracao_sim',
    )
    list_filter = ('data_coleta',)
    search_fields = ('comunidade__nome', 'observacoes')
    date_hierarchy = 'data_coleta'
    autocomplete_fields = ['comunidade']
    list_select_related = ('comunidade',)
    inlines = [AcaoParceiroInline]
    fieldsets = (
        (None, {
            'fields': ('comunidade', 'data_coleta', 'total_produtores',
                       ('qtd_caprinos', 'qtd_ovinos')),
        }),
        (_("Sistemas de criação"), {
            'fields': (('criacao_extensiva', 'criacao_semi_extensiva', 'criacao_intensiva'),),
        }),
        (_("Escrituração zootécnica"), {
            'fields': (('escrituracao_sim', 'escrituracao_nao'),),
        }),
        (_("Nota técnica de campo"), {
            'fields': ('observacoes',),
        }),
    )


@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'qtd_locais', 'qtd_acoes')
    search_fields = ('nome', 'sigla')
    inlines = [LocalParceiroInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _qtd_locais=Count('locais', distinct=True),
            _qtd_acoes=Count('acoes', distinct=True),
        )

    @admin.display(description=_("Localizações"), ordering='_qtd_locais')
    def qtd_locais(self, obj):
        return obj._qtd_locais

    @admin.display(description=_("Ações"), ordering='_qtd_acoes')
    def qtd_acoes(self, obj):
        return obj._qtd_acoes


@admin.register(LocalParceiro)
class LocalParceiroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'parceiro', 'endereco', 'coordenadas')
    list_filter = ('parceiro',)
    search_fields = ('nome', 'endereco', 'parceiro__nome', 'parceiro__sigla')
    autocomplete_fields = ['parceiro']
    list_select_related = ('parceiro',)
    fieldsets = (
        (None, {
            'fields': ('parceiro', 'nome', 'endereco'),
        }),
        (_("Localização"), {
            'fields': (('latitude', 'longitude'),),
            'description': _(
                "Coordenadas em graus decimais (WGS 84). O mapa liga cada "
                "comunidade ao local mais próximo de cada parceiro e mostra a "
                "distância em linha reta."
            ),
        }),
    )

    @admin.display(description=_("Coordenadas"))
    def coordenadas(self, obj):
        return f"{obj.latitude:.4f}, {obj.longitude:.4f}"
