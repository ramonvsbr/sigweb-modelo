"""Modelos espelhando o banco PostGIS do SIGWeb.

Todos são `managed = False`: o esquema vive nos scripts de banco_de_dados/
deste repositório e é aplicado por SQL (criacao_tabelas.sql e migracao_NN_*.sql).
O Django só lê e escreve, para que o admin seja a porta de entrada dos dados do
mapa; as tabelas do próprio Django (usuários, sessões) ficam no mesmo banco.

A coluna `geom` (PostGIS) de propósito NÃO aparece aqui: no banco ela é uma
coluna gerada a partir de latitude/longitude, então o Django nunca deve
escrevê-la — basta gravar os dois números.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Comunidade(models.Model):
    """Comunidade/associação mapeada — o ponto que aparece no mapa."""

    nome = models.CharField(_("Nome"), max_length=150)
    municipio = models.CharField(
        _("Município"), max_length=100, blank=True, null=True,
        help_text=_("Habilita o filtro de município no mapa. Escreva sempre do mesmo jeito."),
    )
    informacoes_adicionais = models.TextField(
        _("Informações adicionais"), blank=True, null=True,
        help_text=_("Texto exibido no painel lateral do mapa, em “Informações de Cadastro”."),
    )
    latitude = models.FloatField(
        _("Latitude"),
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text=_("Graus decimais, negativo no hemisfério sul. Ex.: -9.3845"),
    )
    longitude = models.FloatField(
        _("Longitude"),
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text=_("Graus decimais, negativo a oeste de Greenwich. Ex.: -40.2534"),
    )

    class Meta:
        managed = False
        db_table = 'comunidades'
        ordering = ['nome']
        verbose_name = _("Comunidade")
        verbose_name_plural = _("Comunidades")

    def __str__(self):
        return self.nome

    @property
    def ultima_coleta(self):
        """Coleta mais recente — é ela que o mapa exibe.

        Usa `.all()` para aproveitar o prefetch_related do admin em vez de
        disparar uma query por linha da listagem.
        """
        return next(iter(self.coletas.all()), None)


class ColetaProducao(models.Model):
    """Levantamento zootécnico de uma comunidade numa data.

    Uma comunidade pode ter várias coletas ao longo do tempo; o mapa mostra
    sempre a mais recente (a view vw_comunidades_dashboard faz esse recorte).
    """

    comunidade = models.ForeignKey(
        Comunidade, on_delete=models.CASCADE, related_name='coletas',
        db_column='comunidade_id', verbose_name=_("Comunidade"),
    )
    data_coleta = models.DateField(_("Data da coleta"), default=timezone.localdate)
    total_produtores = models.PositiveIntegerField(_("Total de produtores"), default=0)
    qtd_caprinos = models.PositiveIntegerField(_("Caprinos (cabeças)"), default=0)
    qtd_ovinos = models.PositiveIntegerField(_("Ovinos (cabeças)"), default=0)
    criacao_extensiva = models.PositiveIntegerField(_("Criação extensiva"), default=0)
    criacao_semi_extensiva = models.PositiveIntegerField(_("Criação semi-extensiva"), default=0)
    criacao_intensiva = models.PositiveIntegerField(_("Criação intensiva"), default=0)
    escrituracao_sim = models.PositiveIntegerField(_("Fazem escrituração"), default=0)
    escrituracao_nao = models.PositiveIntegerField(_("Não fazem escrituração"), default=0)
    observacoes = models.TextField(
        _("Observações"), blank=True, null=True,
        help_text=_("Nota técnica de campo, exibida no painel lateral do mapa."),
    )

    class Meta:
        managed = False
        db_table = 'coletas_producao'
        ordering = ['-data_coleta', '-id']
        verbose_name = _("Coleta de produção")
        verbose_name_plural = _("Coletas de produção")

    def __str__(self):
        return f"{self.comunidade} — {self.data_coleta:%d/%m/%Y}"


class Parceiro(models.Model):
    """Instituição parceira (Banco do Nordeste, SEBRAE, SENAR…).

    Catálogo único: ações e localizações apontam para cá, então o mesmo
    parceiro não aparece escrito de jeitos diferentes no mapa.
    """

    nome = models.CharField(_("Nome"), max_length=150, unique=True)
    sigla = models.CharField(
        _("Sigla"), max_length=30, blank=True, null=True,
        help_text=_("Rótulo curto do pino no mapa. Ex.: BNB"),
    )

    class Meta:
        managed = False
        db_table = 'parceiros'
        ordering = ['nome']
        verbose_name = _("Parceiro")
        verbose_name_plural = _("Parceiros")

    def __str__(self):
        return self.nome


class AcaoParceiro(models.Model):
    """O que um parceiro fez na comunidade, registrado junto da coleta."""

    coleta = models.ForeignKey(
        ColetaProducao, on_delete=models.CASCADE, related_name='acoes_parceiros',
        db_column='coleta_id', verbose_name=_("Coleta"),
    )
    # PROTECT espelha o ON DELETE RESTRICT do banco: apagar um parceiro com
    # ações levaria junto o histórico da comunidade.
    parceiro = models.ForeignKey(
        Parceiro, on_delete=models.PROTECT, related_name='acoes',
        db_column='parceiro_id', verbose_name=_("Parceiro"),
    )
    data_acao = models.DateField(_("Data"), default=timezone.localdate)
    descricao = models.TextField(
        _("Ação realizada"),
        help_text=_("Ex.: curso de manejo sanitário, liberação de crédito do Agroamigo."),
    )

    class Meta:
        managed = False
        db_table = 'acoes_parceiros'
        ordering = ['-data_acao', '-id']
        verbose_name = _("Ação de parceiro")
        verbose_name_plural = _("Ações de parceiros")

    def __str__(self):
        return f"{self.parceiro} — {self.data_acao:%d/%m/%Y}"


class LocalParceiro(models.Model):
    """Endereço físico de um parceiro (agência, escritório) — pino no mapa.

    Como em Comunidade, `geom` é coluna gerada no banco a partir de
    latitude/longitude e por isso não aparece aqui.
    """

    parceiro = models.ForeignKey(
        Parceiro, on_delete=models.CASCADE, related_name='locais',
        db_column='parceiro_id', verbose_name=_("Parceiro"),
    )
    nome = models.CharField(
        _("Nome do local"), max_length=150,
        help_text=_("Ex.: Agência Petrolina, Escritório Regional de Juazeiro"),
    )
    endereco = models.CharField(_("Endereço"), max_length=255, blank=True, null=True)
    latitude = models.FloatField(
        _("Latitude"),
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text=_("Graus decimais, negativo no hemisfério sul. Ex.: -9.3845"),
    )
    longitude = models.FloatField(
        _("Longitude"),
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text=_("Graus decimais, negativo a oeste de Greenwich. Ex.: -40.2534"),
    )

    class Meta:
        managed = False
        db_table = 'locais_parceiros'
        ordering = ['parceiro__nome', 'nome']
        verbose_name = _("Localização de parceiro")
        verbose_name_plural = _("Localizações de parceiros")

    def __str__(self):
        return f"{self.parceiro} — {self.nome}"
