# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Páginas principais
    path('', views.index, name='index'),
    path('pesquisar/', views.pesquisar, name='pesquisar'),
    path('lista/', views.lista_estabelecimentos, name='lista_estabelecimentos'),
    
    # Busca por endereço (NOVO)
    path('buscar-endereco/', views.buscar_por_endereco, name='buscar_por_endereco'),
    path('mapa/', views.mapa_postos, name='mapa_postos'),
    path('posto/<int:posto_id>/', views.detalhe_posto, name='detalhe_posto'),
    path('autocomplete-endereco/', views.autocomplete_endereco, name='autocomplete_endereco'),
    
    # Importação e gerenciamento
    path('importar/', views.importar_excel, name='importar_excel'),
    path('adicionar-precos-exemplo/', views.adicionar_precos_exemplo, name='adicionar_precos_exemplo'),
    path('atualizar-precos/', views.atualizar_precos_automatico, name='atualizar_precos_automatico'),
]