# myapp/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q  
from django.contrib import messages
from django.http import JsonResponse
from .models import Estabelecimento, PrecoCombustivel  
import pandas as pd
import random  
import os


# ========== PÁGINAS PRINCIPAIS ==========

def index(request):
    """Página inicial com dashboard"""
    from django.db.models import Avg, Min, Count
    
    # Contadores básicos
    total_postos = Estabelecimento.objects.count()
    total_precos = PrecoCombustivel.objects.count()
    cidades_unicas = Estabelecimento.objects.values('cidade').distinct().count()
    
    # Médias de preços por tipo de combustível
    medias = PrecoCombustivel.objects.values('tipo_combustivel').annotate(
        media=Avg('preco'),
        total=Count('id')
    )
    
    # Dicionário de médias
    medias_dict = {item['tipo_combustivel']: item['media'] for item in medias}
    
    # Postos em destaque (com preços)
    postos_destaque = Estabelecimento.objects.filter(
        precos__isnull=False
    ).distinct()[:8]
    
    # Adiciona preços recentes
    for posto in postos_destaque:
        posto.precos_recentes = get_precos_recentes(posto)
    
    # Postos mais baratos (gasolina comum)
    postos_baratos_query = Estabelecimento.objects.filter(
        precos__tipo_combustivel='GASOLINA_COMUM'
    ).annotate(
        preco_minimo=Min('precos__preco')
    ).order_by('preco_minimo')[:5]
    
    # Formata os postos baratos com outros preços
    postos_baratos = []
    for posto in postos_baratos_query:
        # Busca outros preços deste posto
        outros_precos = {}
        for preco in posto.precos.all().order_by('-data_coleta'):
            if preco.tipo_combustivel != 'GASOLINA_COMUM':
                outros_precos[preco.tipo_combustivel] = str(preco.preco)
        
        postos_baratos.append({
            'id': posto.id,
            'nome_fantasia': posto.nome_fantasia or posto.razao_social,
            'cidade': posto.cidade,
            'uf': posto.uf,
            'bandeira': posto.bandeira,
            'preco_minimo': f"{posto.preco_minimo:.3f}",
            'outros_precos': outros_precos
        })
    
    context = {
        'total_postos': total_postos,
        'total_precos': total_precos,
        'cidades_unicas': cidades_unicas,
        'media_gasolina_comum': f"{medias_dict.get('GASOLINA_COMUM', 0):.3f}",
        'media_gasolina_aditivada': f"{medias_dict.get('GASOLINA_ADITIVADA', 0):.3f}",
        'media_etanol': f"{medias_dict.get('ETANOL', 0):.3f}",
        'media_diesel': f"{medias_dict.get('DIESEL', 0):.3f}",
        'media_diesel_s10': f"{medias_dict.get('DIESEL_S10', 0):.3f}",
        'media_gnv': f"{medias_dict.get('GNV', 0):.3f}",
        'media_gasolina': f"{medias_dict.get('GASOLINA_COMUM', 0):.3f}",
        'postos_destaque': postos_destaque,
        'postos_baratos': postos_baratos,
    }
    
    return render(request, 'myapp/index.html', context)

def pesquisar(request):
    """Busca tradicional (mantenha como está)"""
    query = request.GET.get('q', '')
    tipo_pesquisa = request.GET.get('tipo', 'nome')
    resultados = []

    if query:
        if tipo_pesquisa == 'cnpj':
            cnpj_limpo = ''.join(filter(str.isdigit, query))
            resultados = Estabelecimento.objects.filter(
                cnpj__icontains=cnpj_limpo
            ).prefetch_related('precos')
        
        elif tipo_pesquisa == 'cidade':
            uf = request.GET.get('uf', '')
            if uf:
                resultados = Estabelecimento.objects.filter(
                    Q(cidade__icontains=query) & Q(uf__iexact=uf)
                ).prefetch_related('precos')
            else:
                resultados = Estabelecimento.objects.filter(
                    cidade__icontains=query
                ).prefetch_related('precos')
        
        elif tipo_pesquisa == 'bandeira':
            resultados = Estabelecimento.objects.filter(
                bandeira__icontains=query
            ).prefetch_related('precos')
        
        else:  # Pesquisa por nome (padrão)
            resultados = Estabelecimento.objects.filter(
                Q(nome_fantasia__icontains=query) |
                Q(razao_social__icontains=query) |
                Q(cidade__icontains=query) |
                Q(bairro__icontains=query) |
                Q(endereco__icontains=query)
            ).prefetch_related('precos')

    return render(request, 'myapp/pesquisar.html', {
        'resultados': resultados,
        'query': query,
        'tipo_pesquisa': tipo_pesquisa
    })


def lista_estabelecimentos(request):
    """Lista todos os estabelecimentos"""
    estabelecimentos = Estabelecimento.objects.all().order_by('cidade', 'nome_fantasia')
    return render(request, 'myapp/lista.html', {
        'estabelecimentos': estabelecimentos
    })


# ========== BUSCA POR ENDEREÇO (NOVA FUNCIONALIDADE) ==========
def buscar_por_endereco(request):
    """
    Busca avançada por endereço com múltiplos filtros
    URL: /buscar-endereco/?endereco=Paulista&cidade=São+Paulo&bairro=Bela+Vista
    """
    endereco = request.GET.get('endereco', '').strip()
    cidade = request.GET.get('cidade', '').strip()
    bairro = request.GET.get('bairro', '').strip()
    uf = request.GET.get('uf', '').strip()
    combustivel = request.GET.get('combustivel', '').strip()
    raio = request.GET.get('raio', '').strip()
    
    # Inicia com todos os estabelecimentos
    resultados = Estabelecimento.objects.all()
    
    # Aplica filtros cumulativos
    if endereco:
        resultados = resultados.filter(endereco__icontains=endereco)
    
    if cidade:
        resultados = resultados.filter(cidade__icontains=cidade)
    
    if bairro:
        resultados = resultados.filter(bairro__icontains=bairro)
    
    if uf:
        resultados = resultados.filter(uf__iexact=uf.upper())
    
    # Filtro por tipo de combustível
    if combustivel:
        estabelecimentos_com_combustivel = PrecoCombustivel.objects.filter(
            tipo_combustivel=combustivel
        ).values_list('estabelecimento_id', flat=True).distinct()
        
        resultados = resultados.filter(id__in=estabelecimentos_com_combustivel)
    
    # Filtro por raio (se tiver coordenadas)
    if raio and request.GET.get('lat') and request.GET.get('lng'):
        try:
            lat = float(request.GET.get('lat'))
            lng = float(request.GET.get('lng'))
            raio_km = float(raio)
            
            # Filtra postos com coordenadas
            resultados_com_coordenadas = resultados.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )
            
            # Aqui você poderia implementar cálculo de distância
            # Por enquanto, vamos apenas marcar quais têm coordenadas
            resultados = resultados_com_coordenadas
            
        except (ValueError, TypeError):
            pass
    
    # Ordenação
    resultados = resultados.order_by('cidade', 'bairro', 'nome_fantasia')
    
    # Adiciona preços recentes a cada resultado
    for estabelecimento in resultados:
        estabelecimento.precos_recentes = get_precos_recentes(estabelecimento)
    
    context = {
        'resultados': resultados,
        'total': resultados.count(),
        'filtros': {
            'endereco': endereco,
            'cidade': cidade,
            'bairro': bairro,
            'uf': uf,
            'combustivel': combustivel,
            'raio': raio,
        },
        'TIPO_COMBUSTIVEL': PrecoCombustivel.TIPO_COMBUSTIVEL,
        'UFS_BRASIL': get_ufs_brasil(),
    }
    
    return render(request, 'myapp/buscar_endereco.html', context)

def mapa_postos(request):
    """Página com mapa mostrando postos por localização"""
    from django.core import serializers
    import json
    
    # Filtra postos com coordenadas
    postos = Estabelecimento.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )[:200]  # Limita para performance
    
    # Prepara dados para o mapa
    postos_data = []
    for posto in postos:
        # Preços formatados
        precos_dict = {}
        for preco_obj in posto.precos.all()[:3]:  # Pega até 3 preços
            precos_dict[preco_obj.tipo_combustivel] = str(preco_obj.preco)
        
        postos_data.append({
            'id': posto.id,
            'nome': posto.nome_fantasia or posto.razao_social,
            'endereco': posto.endereco,
            'bairro': posto.bairro,
            'cidade': posto.cidade,
            'uf': posto.uf,
            'bandeira': posto.bandeira or 'Independiente',
            'latitude': float(posto.latitude),
            'longitude': float(posto.longitude),
            'precos': precos_dict,
        })
    
    context = {
        'postos': json.dumps(postos_data),  # Converte para JSON seguro
        'total_postos': len(postos_data),
    }
    
    return render(request, 'myapp/mapa.html', context)


def detalhe_posto(request, posto_id):
    """Página de detalhes de um posto específico"""
    posto = get_object_or_404(Estabelecimento, id=posto_id)
    
    # Preços agrupados por tipo
    precos = posto.precos.all().order_by('-data_coleta')
    precos_por_tipo = {}
    
    for preco in precos:
        if preco.tipo_combustivel not in precos_por_tipo:
            precos_por_tipo[preco.tipo_combustivel] = []
        precos_por_tipo[preco.tipo_combustivel].append(preco)
    
    # Preços recentes para sidebar
    precos_recentes = get_precos_recentes(posto)
    
    context = {
        'posto': posto,
        'precos_por_tipo': precos_por_tipo,
        'precos_recentes': precos_recentes,
        'TIPO_COMBUSTIVEL': dict(PrecoCombustivel.TIPO_COMBUSTIVEL),
    }
    
    return render(request, 'myapp/detalhe_posto.html', context)


# ========== FUNÇÕES AUXILIARES ==========
def get_precos_recentes(estabelecimento):
    """Retorna os preços mais recentes de cada tipo de combustível"""
    precos_recentes = {}
    for tipo in ['GASOLINA_COMUM', 'GASOLINA_ADITIVADA', 'ETANOL', 'DIESEL', 'DIESEL_S10', 'GNV']:
        try:
            ultimo_preco = estabelecimento.precos.filter(
                tipo_combustivel=tipo
            ).latest('data_coleta')
            precos_recentes[tipo] = {
                'preco': ultimo_preco.preco,
                'data': ultimo_preco.data_coleta,
                'fonte': ultimo_preco.fonte,
            }
        except PrecoCombustivel.DoesNotExist:
            precos_recentes[tipo] = None
    return precos_recentes


def get_ufs_brasil():
    """Retorna lista de UFs do Brasil"""
    return [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]


def autocomplete_endereco(request):
    """Para autocomplete na busca de endereços"""
    term = request.GET.get('term', '').strip()
    
    if len(term) >= 2:
        suggestions = []
        
        # Cidades
        cidades = Estabelecimento.objects.filter(
            cidade__icontains=term
        ).values_list('cidade', flat=True).distinct()[:5]
        
        for cidade in cidades:
            suggestions.append({
                'label': f'🏙️ {cidade}',
                'value': cidade,
                'type': 'cidade'
            })
        
        # Bairros
        bairros = Estabelecimento.objects.filter(
            bairro__icontains=term
        ).values_list('bairro', flat=True).distinct()[:5]
        
        for bairro in bairros:
            suggestions.append({
                'label': f'📍 {bairro}',
                'value': bairro,
                'type': 'bairro'
            })
        
        # Endereços
        enderecos = Estabelecimento.objects.filter(
            endereco__icontains=term
        ).values_list('endereco', flat=True).distinct()[:5]
        
        for endereco in enderecos:
            suggestions.append({
                'label': f'🏠 {endereco[:50]}...',
                'value': endereco,
                'type': 'endereco'
            })
        
        return JsonResponse(suggestions, safe=False)
    
    return JsonResponse([], safe=False)


# ========== IMPORTAÇÃO E GERENCIAMENTO ==========
def importar_excel(request):
    """Importa estabelecimentos de arquivo Excel"""
    if request.method == 'POST' and request.FILES.get('arquivo_excel'):
        arquivo = request.FILES['arquivo_excel']
        
        try:
            if arquivo.name.endswith('.xlsb'):
                df = pd.read_excel(arquivo, engine='pyxlsb')
            elif arquivo.name.endswith('.xlsx') or arquivo.name.endswith('.xls'):
                df = pd.read_excel(arquivo)
            else:
                messages.error(request, '❌ Formato não suportado. Use .xlsx, .xls ou .xlsb.')
                return render(request, 'myapp/importar.html')
            
            total_importados = 0
            estabelecimentos_batch = []
            
            for _, row in df.iterrows():
                try:
                    cnpj = str(row['CNPJ']).strip() if pd.notna(row['CNPJ']) else ''
                    if not cnpj:
                        continue
                    
                    estabelecimento = Estabelecimento(
                        cnpj=cnpj,
                        razao_social=str(row.get('RAZAO_SOCIAL', '')).strip()[:200],
                        nome_fantasia=str(row.get('NOME_FANTASIA', '')).strip()[:200] or str(row.get('RAZAO_SOCIAL', '')).strip()[:200],
                        bandeira=str(row.get('BANDEIRA', '')).strip()[:100],
                        endereco=str(row.get('ENDERECO', '')).strip()[:300],
                        bairro=str(row.get('BAIRRO', '')).strip()[:100],
                        cidade=str(row.get('MUNICIPIO', row.get('CIDADE', ''))).strip()[:100],
                        uf=str(row.get('UF', '')).strip()[:2].upper(),
                        cep=str(row.get('CEP', '')).strip()[:10],
                    )
                    
                    estabelecimentos_batch.append(estabelecimento)
                    
                    if len(estabelecimentos_batch) >= 500:
                        Estabelecimento.objects.bulk_create(estabelecimentos_batch, ignore_conflicts=True)
                        total_importados += len(estabelecimentos_batch)
                        estabelecimentos_batch = []
                        
                except Exception as e:
                    continue
            
            if estabelecimentos_batch:
                Estabelecimento.objects.bulk_create(estabelecimentos_batch, ignore_conflicts=True)
                total_importados += len(estabelecimentos_batch)
            
            messages.success(request, f'✅ {total_importados} estabelecimentos importados!')
            
        except Exception as e:
            messages.error(request, f'❌ Erro: {str(e)}')
    
    return render(request, 'myapp/importar.html')


def adicionar_precos_exemplo(request):
    """Adiciona preços de exemplo"""
    try:
        precos_base = {
            'Shell': {'GASOLINA_COMUM': 5.89, 'GASOLINA_ADITIVADA': 6.09, 'ETANOL': 4.29, 'DIESEL': 5.99},
            'Ipiranga': {'GASOLINA_COMUM': 5.79, 'GASOLINA_ADITIVADA': 5.99, 'ETANOL': 4.19, 'DIESEL': 5.89},
            'BR': {'GASOLINA_COMUM': 5.75, 'GASOLINA_ADITIVADA': 5.95, 'DIESEL': 5.85, 'DIESEL_S10': 6.05},
            'Ale': {'GASOLINA_COMUM': 5.69, 'ETANOL': 4.09, 'DIESEL': 5.79},
            'Petrobras': {'GASOLINA_COMUM': 5.82, 'GASOLINA_ADITIVADA': 6.02, 'ETANOL': 4.22, 'DIESEL': 5.92},
        }
        
        estabelecimentos = Estabelecimento.objects.filter(precos__isnull=True)[:200]
        total_precos = 0
        
        for estabelecimento in estabelecimentos:
            bandeira = estabelecimento.bandeira or 'Shell'
            precos_bandeira = precos_base.get(bandeira, precos_base['Shell'])
            
            for tipo_combustivel, preco_base in precos_bandeira.items():
                variacao = random.uniform(0.95, 1.05)
                preco_final = round(preco_base * variacao, 3)
                
                PrecoCombustivel.objects.create(
                    estabelecimento=estabelecimento,
                    tipo_combustivel=tipo_combustivel,
                    preco=preco_final,
                    fonte='Sistema (exemplo)'
                )
                total_precos += 1
        
        messages.success(request, f'✅ {total_precos} preços adicionados para {len(estabelecimentos)} estabelecimentos!')
    
    except Exception as e:
        messages.error(request, f'❌ Erro: {str(e)}')
    
    return render(request, 'myapp/index.html')


def atualizar_precos_automatico(request):
    """Atualiza preços automaticamente"""
    try:
        precos_base = {
            'Shell': {'GASOLINA_COMUM': 5.89, 'GASOLINA_ADITIVADA': 6.09, 'ETANOL': 4.29, 'DIESEL': 5.99},
            'Ipiranga': {'GASOLINA_COMUM': 5.79, 'GASOLINA_ADITIVADA': 5.99, 'ETANOL': 4.19, 'DIESEL': 5.89},
            'BR': {'GASOLINA_COMUM': 5.75, 'GASOLINA_ADITIVADA': 5.95, 'ETANOL': 4.15, 'DIESEL': 5.85},
            'Ale': {'GASOLINA_COMUM': 5.69, 'GASOLINA_ADITIVADA': 5.89, 'ETANOL': 4.09, 'DIESEL': 5.79},
            'Petrobras': {'GASOLINA_COMUM': 5.82, 'GASOLINA_ADITIVADA': 6.02, 'ETANOL': 4.22, 'DIESEL': 5.92},
        }
        
        estabelecimentos_sem_preco = Estabelecimento.objects.filter(precos__isnull=True)[:500]
        total_adicionados = 0
        
        for estabelecimento in estabelecimentos_sem_preco:
            bandeira = estabelecimento.bandeira or 'Shell'
            precos_bandeira = precos_base.get(bandeira, precos_base['Shell'])
            
            tipos_combustivel = list(precos_bandeira.keys())[:random.randint(2, 3)]
            
            for tipo in tipos_combustivel:
                variacao = random.uniform(0.97, 1.03)
                preco_final = round(precos_bandeira[tipo] * variacao, 3)
                
                PrecoCombustivel.objects.create(
                    estabelecimento=estabelecimento,
                    tipo_combustivel=tipo,
                    preco=preco_final,
                    fonte='Atualização Automática'
                )
                total_adicionados += 1
        
        messages.success(request, f'✅ {total_adicionados} preços adicionados automaticamente!')
        
    except Exception as e:
        messages.error(request, f'❌ Erro: {str(e)}')
    
    return render(request, 'myapp/index.html')