# myapp/models.py
from django.db import models

class Estabelecimento(models.Model):
    cnpj = models.CharField(max_length=20, unique=True)
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True)      
    bandeira = models.CharField(max_length=100, blank=True, null=True)
    endereco = models.CharField(max_length=300)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)
    
    # Campos de geolocalização simples
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Ex: -23.550650"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Ex: -46.633382"
    )
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social
    
    @property
    def coordenadas(self):
        if self.latitude and self.longitude:
            return (float(self.latitude), float(self.longitude))
        return None
    
    @property
    def endereco_completo(self):
        return f"{self.endereco}, {self.bairro}, {self.cidade} - {self.uf}, {self.cep}"
    
    @property
    def ultimos_precos(self):
        """Retorna os preços mais recentes por tipo de combustível"""
        from .models import PrecoCombustivel
        precos = {}
        for tipo in ['GASOLINA_COMUM', 'GASOLINA_ADITIVADA', 'ETANOL', 'DIESEL']:
            try:
                ultimo = self.precos.filter(tipo_combustivel=tipo).latest('data_coleta')
                precos[tipo] = ultimo.preco
            except PrecoCombustivel.DoesNotExist:
                precos[tipo] = None
        return precos

    class Meta:
        verbose_name = 'Estabelecimento'
        verbose_name_plural = 'Estabelecimentos'
        ordering = ['cidade', 'nome_fantasia']


class PrecoCombustivel(models.Model):
    TIPO_COMBUSTIVEL = [
        ('GASOLINA_COMUM', 'Gasolina Comum'),
        ('GASOLINA_ADITIVADA', 'Gasolina Aditivada'),
        ('ETANOL', 'Etanol'),
        ('DIESEL', 'Diesel'),
        ('DIESEL_S10', 'Diesel S10'),
        ('GNV', 'GNV'),
    ]
    
    estabelecimento = models.ForeignKey(
        Estabelecimento, 
        on_delete=models.CASCADE, 
        related_name='precos'
    )
    tipo_combustivel = models.CharField(max_length=20, choices=TIPO_COMBUSTIVEL)
    preco = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    data_coleta = models.DateTimeField(auto_now_add=True)
    fonte = models.CharField(max_length=100, default='Sistema')
    
    def __str__(self):
        estabelecimento_nome = self.estabelecimento.nome_fantasia or self.estabelecimento.razao_social
        return f'{estabelecimento_nome} - {self.get_tipo_combustivel_display()} - R$ {self.preco}'

    class Meta:
        verbose_name = 'Preço de Combustível'
        verbose_name_plural = 'Preços de Combustíveis'
        ordering = ['-data_coleta']