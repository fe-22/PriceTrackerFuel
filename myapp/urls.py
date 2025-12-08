# myapp/urls.py - VERSÃO FUNCIONAL
from django.urls import path
from . import views

urlpatterns = [
    # Páginas principais
    path('', views.index, name='index'),
    path('pesquisar/', views.pesquisar, name='pesquisar'),
    path('lista/', views.lista_estabelecimentos, name='lista_estabelecimentos'),
    
    # Busca por endereço
    path('buscar-endereco/', views.buscar_por_endereco, name='buscar_por_endereco'),
    path('mapa/', views.mapa_postos, name='mapa_postos'),
    path('posto/<int:posto_id>/', views.detalhe_posto, name='detalhe_posto'),
    path('autocomplete-endereco/', views.autocomplete_endereco, name='autocomplete_endereco'),
    
    # Importação e gerenciamento
    path('importar/', views.importar_excel, name='importar_excel'),
    path('adicionar-precos-exemplo/', views.adicionar_precos_exemplo, name='adicionar_precos_exemplo'),
    path('atualizar-precos/', views.atualizar_precos_automatico, name='atualizar_precos_automatico'),
    
    # Scraping
    path('scraping/', views.scraping_precos, name='scraping_precos'),
    path('scraping/api/', views.api_scraping_precos, name='api_scraping'),
    path('scraping/dashboard/', views.dashboard_scraping, name='dashboard_scraping'),
    
    # APIs adicionais (opcionais)
    path('api/postos/', views.api_lista_postos, name='api_postos_lista'),
    path('api/postos/<int:posto_id>/', views.api_detalhe_posto, name='api_posto_detalhe'),
]

"""
URL Configuration for PriceTracker Fuel

Páginas principais:
- /                     -> Página inicial
- /postos/              -> Lista de postos
- /postos/mapa/         -> Mapa interativo
- /postos/<id>/         -> Detalhes do posto

Buscas:
- /busca/               -> Busca avançada
- /busca/endereco/      -> Busca por endereço

Gerenciamento:
- /gerenciar/importar/          -> Importar dados
- /gerenciar/precos-exemplo/    -> Adicionar dados exemplo
- /gerenciar/atualizar-precos/  -> Atualizar preços

Scraping:
- /scraping/                    -> Interface de scraping
- /scraping/dashboard/          -> Dashboard de scraping

APIs:
- /api/autocomplete/            -> Autocomplete de endereços
- /api/scraping/executar/       -> Executar scraping (POST)
- /api/postos/                  -> Lista de postos (JSON)
- /api/postos/<id>/             -> Detalhes do posto (JSON)
"""