from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pesquisar/', views.pesquisar, name='pesquisar'),
    path('listar/', views.lista_estabelecimentos, name='lista'),
    path('importar/', views.importar_excel, name='importar'),
    # NOVAS URLs
    path('adicionar-precos/', views.adicionar_precos_exemplo, name='adicionar_precos'),
    path('buscar-precos-anp/<str:cnpj>/', views.buscar_precos_anp, name='buscar_precos_anp'),
    path('atualizar-precos/', views.atualizar_precos_automatico, name='atualizar_precos'),
]