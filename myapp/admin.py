from django.contrib import admin
from .models import Estabelecimento

@admin.register(Estabelecimento)
class EstabelecimentoAdmin(admin.ModelAdmin):
    list_display = ['nome_fantasia', 'cidade', 'uf', 'bandeira']
    search_fields = ['nome_fantasia', 'razao_social', 'cidade']
    list_filter = ['uf', 'bandeira']

