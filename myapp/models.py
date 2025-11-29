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
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social

    class Meta:
        verbose_name = 'Estabelecimento'
        verbose_name_plural = 'Estabelecimentos'

class PrecoCombustivel(models.Model):
    TIPO_COMBUSTIVEL = [
        ('GASOLINA_COMUM', 'Gasolina Comum'),
        ('GASOLINA_ADITIVADA', 'Gasolina Aditivada'),
        ('ETANOL', 'Etanol'),
        ('DIESEL', 'Diesel'),
        ('DIESEL_S10', 'Diesel S10'),
        ('GNV', 'GNV'),
    ]
    
    estabelecimento = models.ForeignKey(Estabelecimento, on_delete=models.CASCADE, related_name='precos')
    tipo_combustivel = models.CharField(max_length=20, choices=TIPO_COMBUSTIVEL)
    preco = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    data_coleta = models.DateTimeField(auto_now_add=True)
    fonte = models.CharField(max_length=100, default='Sistema')
    
    def __str__(self):
        return f'{self.estabelecimento.nome_fantasia} - {self.get_tipo_combustivel_display()} - R$ {self.preco}'

    class Meta:
        verbose_name = 'Preço de Combustível'
        verbose_name_plural = 'Preços de Combustíveis'
        ordering = ['-data_coleta']
