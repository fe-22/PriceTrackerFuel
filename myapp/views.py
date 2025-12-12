from django.conf import settings
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
import pandas as pd
import io
import random
from datetime import datetime, timedelta
from django.utils import timezone

# View principal
def index(request):
    context = {
        'total_postos': 0,
        'total_precos': 0,
        'cidades_unicas': 0,
        'media_gasolina': "6.50",
        'media_etanol': "4.20",
        'media_diesel': "5.80",
        'media_gasolina_comum': "6.50",
        'media_gasolina_aditivada': "6.70",
        'media_diesel_s10': "6.00",
        'media_gnv': "4.50",
        'postos_destaque': [],
        'postos_baratos': [],
    }
    
    try:
        from .models import Estabelecimento, PrecoCombustivel
        context['total_postos'] = Estabelecimento.objects.count()
        context['total_precos'] = PrecoCombustivel.objects.count()
        
        if context['total_postos'] > 0:
            context['cidades_unicas'] = Estabelecimento.objects.values('cidade').distinct().count()
    except Exception as e:
        print(f"⚠️ Erro ao carregar dados: {e}")
    
    return render(request, 'myapp/index.html', context)


def pesquisar(request):
    """Página de pesquisa avançada de postos"""
    from .models import Estabelecimento
    
    query = request.GET.get('q', '').strip()
    tipo_pesquisa = request.GET.get('tipo', 'nome')
    resultados = []
    total_encontrado = 0
    
    if query:
        try:
            if tipo_pesquisa == 'cnpj':
                cnpj_limpo = ''.join(filter(str.isdigit, query))
                if cnpj_limpo:
                    resultados = Estabelecimento.objects.filter(
                        cnpj__icontains=cnpj_limpo
                    ).prefetch_related('precos')
            
            elif tipo_pesquisa == 'cidade':
                uf = request.GET.get('uf', '').strip().upper()
                if uf:
                    resultados = Estabelecimento.objects.filter(
                        Q(cidade__icontains=query) & Q(uf=uf)
                    ).prefetch_related('precos')
                else:
                    resultados = Estabelecimento.objects.filter(
                        cidade__icontains=query
                    ).prefetch_related('precos')
            
            elif tipo_pesquisa == 'bandeira':
                resultados = Estabelecimento.objects.filter(
                    bandeira__icontains=query
                ).prefetch_related('precos')
            
            else:  # Pesquisa por nome
                resultados = Estabelecimento.objects.filter(
                    Q(nome_fantasia__icontains=query) |
                    Q(razao_social__icontains=query) |
                    Q(endereco__icontains=query) |
                    Q(bairro__icontains=query)
                ).prefetch_related('precos')
            
            total_encontrado = resultados.count()
            
            for estabelecimento in resultados:
                estabelecimento.precos_recentes = {}
                precos_recentes = estabelecimento.precos.all().order_by('-data_coleta')[:3]
                for preco in precos_recentes:
                    estabelecimento.precos_recentes[preco.tipo_combustivel] = {
                        'preco': preco.preco,
                        'data': preco.data_coleta,
                        'fonte': preco.fonte
                    }
                    
        except Exception as e:
            print(f"⚠️ Erro na pesquisa: {e}")
    
    UFS_BRASIL = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    context = {
        'query': query,
        'tipo_pesquisa': tipo_pesquisa,
        'resultados': resultados,
        'total_encontrado': total_encontrado,
        'UFS_BRASIL': UFS_BRASIL,
        'tipos_pesquisa': [
            ('nome', 'Nome/Razão Social'),
            ('cnpj', 'CNPJ'),
            ('cidade', 'Cidade'),
            ('bandeira', 'Bandeira'),
        ]
    }
    
    return render(request, 'myapp/pesquisar.html', context)


def lista_estabelecimentos(request):
    """Lista todos os estabelecimentos"""
    try:
        from .models import Estabelecimento
        estabelecimentos = Estabelecimento.objects.all().order_by('cidade', 'nome_fantasia')
    except Exception as e:
        print(f"⚠️ Erro ao carregar estabelecimentos: {e}")
        estabelecimentos = []
    
    context = {
        'estabelecimentos': estabelecimentos,
    }
    
    return render(request, 'myapp/lista.html', context)


def buscar_por_endereco(request):
    """Busca avançada por endereço"""
    from .models import Estabelecimento
    
    endereco = request.GET.get('endereco', '').strip()
    cidade = request.GET.get('cidade', '').strip()
    bairro = request.GET.get('bairro', '').strip()
    uf = request.GET.get('uf', '').strip()
    combustivel = request.GET.get('combustivel', '').strip()
    
    resultados = Estabelecimento.objects.all()
    
    if endereco:
        resultados = resultados.filter(endereco__icontains=endereco)
    if cidade:
        resultados = resultados.filter(cidade__icontains=cidade)
    if bairro:
        resultados = resultados.filter(bairro__icontains=bairro)
    if uf:
        resultados = resultados.filter(uf=uf)
    if combustivel:
        resultados = resultados.filter(precos__tipo_combustivel=combustivel)
    
    resultados = resultados.distinct().order_by('cidade', 'nome_fantasia')
    
    UFS_BRASIL = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    TIPO_COMBUSTIVEL = [
        ('GASOLINA_COMUM', 'Gasolina Comum'),
        ('GASOLINA_ADITIVADA', 'Gasolina Aditivada'),
        ('ETANOL', 'Etanol'),
        ('DIESEL', 'Diesel'),
        ('DIESEL_S10', 'Diesel S10'),
        ('GNV', 'GNV'),
    ]
    
    context = {
        'endereco': endereco,
        'cidade': cidade,
        'bairro': bairro,
        'uf': uf,
        'combustivel': combustivel,
        'UFS_BRASIL': UFS_BRASIL,
        'TIPO_COMBUSTIVEL': TIPO_COMBUSTIVEL,
        'resultados': resultados,
        'total': resultados.count(),
    }
    
    return render(request, 'myapp/buscar_endereco.html', context)

def mapa_postos(request):
    """View para exibir mapa de postos - VERSÃO INTELIGENTE"""
    try:
        from .models import Estabelecimento
        import json
        import random
        
        print(f"🔍 [MAPA] Iniciando busca de postos...")
        
        # PRIMEIRO: Busca postos REAIS do banco
        postos_reais_queryset = Estabelecimento.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        postos_validos = []
        postos_reais_count = 0
        
        # Tenta carregar dados reais
        for estabelecimento in postos_reais_queryset[:800]:  # Limite razoável
            try:
                # Converte para string primeiro
                lat_str = str(estabelecimento.latitude).strip() if estabelecimento.latitude else ""
                lng_str = str(estabelecimento.longitude).strip() if estabelecimento.longitude else ""
                
                if not lat_str or not lng_str:
                    continue
                
                # Substitui vírgula por ponto para garantir conversão
                lat_str = lat_str.replace(',', '.')
                lng_str = lng_str.replace(',', '.')
                
                lat = float(lat_str)
                lng = float(lng_str)
                
                # Validação básica
                if lat == 0 and lng == 0:
                    continue
                
                # Adiciona aos válidos
                postos_validos.append({
                    'id': estabelecimento.id,
                    'nome': estabelecimento.nome_fantasia or estabelecimento.razao_social or f'Posto {estabelecimento.id}',
                    'endereco': estabelecimento.endereco or '',
                    'cidade': estabelecimento.cidade or '',
                    'uf': estabelecimento.uf or '',
                    'latitude': lat,
                    'longitude': lng,
                    'bandeira': estabelecimento.bandeira or '',
                    'is_demo': False,  # DADO REAL!
                })
                postos_reais_count += 1
                
            except (ValueError, TypeError, AttributeError):
                continue
        
        print(f"✅ [MAPA] Encontrados {postos_reais_count} postos reais no banco")
        
        # DECISÃO: Se tem muitos postos reais, usa só eles
        # Se tem poucos, complementa com dados demo
        if postos_reais_count >= 100:
            # Tem dados suficientes, usa só os reais
            print(f"📊 [MAPA] Usando apenas dados reais ({postos_reais_count} postos)")
        else:
            # Poucos dados reais, complementa com demo
            print(f"⚠️ [MAPA] Apenas {postos_reais_count} postos reais. Complementando...")
            
            # Coordenadas de cidades brasileiras (30 principais)
            cidades_brasil = [
                (-23.5505, -46.6333, 'São Paulo', 'SP'),
                (-15.7797, -47.9297, 'Brasília', 'DF'),
                (-22.9068, -43.1729, 'Rio de Janeiro', 'RJ'),
                (-19.9167, -43.9345, 'Belo Horizonte', 'MG'),
                (-30.0331, -51.2300, 'Porto Alegre', 'RS'),
                (-3.7172, -38.5433, 'Fortaleza', 'CE'),
                (-8.0476, -34.8770, 'Recife', 'PE'),
                (-12.9714, -38.5014, 'Salvador', 'BA'),
                (-1.4558, -48.4902, 'Belém', 'PA'),
                (-16.6869, -49.2648, 'Goiânia', 'GO'),
                (-27.5954, -48.5480, 'Florianópolis', 'SC'),
                (-5.7950, -35.2094, 'Natal', 'RN'),
                (-9.6667, -35.7167, 'Maceió', 'AL'),
                (-20.3194, -40.3378, 'Vitória', 'ES'),
                (-21.1750, -47.8103, 'Ribeirão Preto', 'SP'),
                (-3.1019, -60.0250, 'Manaus', 'AM'),
                (-10.9472, -37.0731, 'Aracaju', 'SE'),
                (-7.2307, -35.8817, 'João Pessoa', 'PB'),
                (-20.4697, -54.6201, 'Campo Grande', 'MS'),
                (-11.6842, -43.4328, 'Teresina', 'PI'),
                (-23.3045, -51.1696, 'Londrina', 'PR'),
                (-22.1200, -51.3900, 'Presidente Prudente', 'SP'),
                (-29.1686, -51.1794, 'Caxias do Sul', 'RS'),
                (-23.9608, -46.3339, 'Santos', 'SP'),
                (-25.4296, -49.2713, 'Curitiba', 'PR'),
                (-22.2528, -54.8167, 'Dourados', 'MS'),
                (-8.7612, -63.9039, 'Porto Velho', 'RO'),
                (-9.9747, -67.8100, 'Rio Branco', 'AC'),
                (-2.5283, -44.3044, 'São Luís', 'MA'),
                (-18.9113, -48.2622, 'Uberlândia', 'MG'),
            ]
            
            bandeiras = ['Shell', 'Ipiranga', 'BR', 'Petrobras', 'Ale', 'Raizen', 'Vale', 'Ativo', 'Texaco']
            
            # Quantos postos demo adicionar?
            postos_demo_needed = max(50, 200 - postos_reais_count)  # Mínimo 50, máximo até 200 total
            
            for i in range(postos_demo_needed):
                cidade_idx = i % len(cidades_brasil)
                lat_base, lng_base, cidade_base, uf_base = cidades_brasil[cidade_idx]
                
                # Adiciona variação
                lat = lat_base + random.uniform(-0.15, 0.15)
                lng = lng_base + random.uniform(-0.15, 0.15)
                bandeira = bandeiras[i % len(bandeiras)]
                
                postos_validos.append({
                    'id': 900000 + i,  # IDs altos para não conflitar
                    'nome': f'Posto {bandeira} {cidade_base}',
                    'endereco': f'Av. Principal, {1000 + (i % 100)}',
                    'cidade': cidade_base,
                    'uf': uf_base,
                    'latitude': round(lat, 6),
                    'longitude': round(lng, 6),
                    'bandeira': bandeira,
                    'is_demo': True,
                })
            
            print(f"📍 [MAPA] Adicionados {postos_demo_needed} postos de demonstração")
        
        print(f"📤 [MAPA] Total final: {len(postos_validos)} postos")
        
        # Bandas disponíveis
        bandeiras_disponiveis = list(set(p['bandeira'] for p in postos_validos if p['bandeira']))
        if not bandeiras_disponiveis:
            bandeiras_disponiveis = ['Shell', 'Ipiranga', 'BR']
        
        # JSON
        postos_json = json.dumps(postos_validos, default=str, ensure_ascii=False)
        
        # Conta dados reais vs demo
        dados_reais = len([p for p in postos_validos if not p.get('is_demo', False)])
        dados_demo = len([p for p in postos_validos if p.get('is_demo', False)])
        
        context = {
            'postos_json': postos_json,
            'total_postos': len(postos_validos),
            'bandeiras': sorted(bandeiras_disponiveis),
            'debug_mode': settings.DEBUG,
            'has_real_data': dados_reais > 0,
            'dados_reais_count': dados_reais,
            'dados_demo_count': dados_demo,
        }
        
        return render(request, 'myapp/mapa.html', context)
        
    except Exception as e:
        print(f"❌ [MAPA] ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback MÍNIMO garantido
        postos_data = [
            {
                'id': 1,
                'nome': 'Posto Shell Centro',
                'latitude': -15.7797,
                'longitude': -47.9297,
                'endereco': 'Eixo Monumental, 1000',
                'cidade': 'Brasília',
                'uf': 'DF',
                'bandeira': 'Shell',
                'is_demo': True,
            },
            {
                'id': 2,
                'nome': 'Posto Ipiranga Norte',
                'latitude': -15.7897,
                'longitude': -47.9397,
                'endereco': 'Asa Norte, 500',
                'cidade': 'Brasília',
                'uf': 'DF',
                'bandeira': 'Ipiranga',
                'is_demo': True,
            },
            {
                'id': 3,
                'nome': 'Posto BR Sul',
                'latitude': -15.7997,
                'longitude': -47.9497,
                'endereco': 'Asa Sul, 300',
                'cidade': 'Brasília',
                'uf': 'DF',
                'bandeira': 'BR',
                'is_demo': True,
            },
        ]
        
        context = {
            'postos_json': json.dumps(postos_data),
            'total_postos': len(postos_data),
            'bandeiras': ['Shell', 'Ipiranga', 'BR'],
            'debug_mode': True,
            'has_real_data': False,
            'dados_reais_count': 0,
            'dados_demo_count': len(postos_data),
        }
        
        return render(request, 'myapp/mapa.html', context)

def api_postos_mapa(request):
    """API para carregar postos no mapa com filtros e paginação"""
    try:
        from .models import Estabelecimento, PrecoCombustivel
        from django.db.models import Prefetch
        
        # Parâmetros de filtro
        bounds = request.GET.get('bounds')  # ne_lat,ne_lng,sw_lat,sw_lng
        zoom = request.GET.get('zoom', 10)
        bandeira = request.GET.get('bandeira')
        combustivel = request.GET.get('combustivel')
        limite = int(request.GET.get('limit', 100))  # Limite por requisição
        
        # Query base
        estabelecimentos = Estabelecimento.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Filtro por bandeira
        if bandeira and bandeira != 'todas':
            estabelecimentos = estabelecimentos.filter(bandeira__iexact=bandeira)
        
        # Filtro por área visível (bounds)
        if bounds:
            try:
                ne_lat, ne_lng, sw_lat, sw_lng = map(float, bounds.split(','))
                estabelecimentos = estabelecimentos.filter(
                    latitude__range=(sw_lat, ne_lat),
                    longitude__range=(sw_lng, ne_lng)
                )
            except:
                pass
        
        # Otimização: prefetch dos últimos preços
        estabelecimentos = estabelecimentos.prefetch_related(
            Prefetch(
                'precos',
                queryset=PrecoCombustivel.objects.order_by('-data_coleta')[:3],
                to_attr='ultimos_precos'
            )
        )[:limite]  # IMPORTANTE: Limite de resultados
        
        # Constrói resposta
        postos_data = []
        for estabelecimento in estabelecimentos:
            precos_dict = {}
            for preco in getattr(estabelecimento, 'ultimos_precos', []):
                precos_dict[preco.tipo_combustivel] = {
                    'preco': float(preco.preco),
                    'data': preco.data_coleta.strftime('%d/%m') if preco.data_coleta else '',
                    'fonte': preco.fonte
                }
            
            postos_data.append({
                'id': estabelecimento.id,
                'nome': estabelecimento.nome_fantasia or estabelecimento.razao_social or 'Posto',
                'endereco': estabelecimento.endereco or '',
                'cidade': estabelecimento.cidade or '',
                'uf': estabelecimento.uf or '',
                'latitude': float(estabelecimento.latitude),
                'longitude': float(estabelecimento.longitude),
                'bandeira': estabelecimento.bandeira or '',
                'precos': precos_dict,
                'has_details': True if estabelecimento.ultimos_precos else False
            })
        
        return JsonResponse({
            'success': True,
            'count': len(postos_data),
            'total': estabelecimentos.count(),
            'postos': postos_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'postos': []
        }, status=500)
        
def api_precos_posto(request, posto_id):
    """API para carregar preços de um posto específico"""
    try:
        from .models import PrecoCombustivel
        
        precos = PrecoCombustivel.objects.filter(
            estabelecimento_id=posto_id
        ).order_by('-data_coleta')[:10]
        
        precos_data = []
        for preco in precos:
            precos_data.append({
                'tipo': preco.tipo_combustivel,
                'tipo_display': preco.get_tipo_combustivel_display(),
                'preco': float(preco.preco),
                'data': preco.data_coleta.strftime('%d/%m/%Y %H:%M') if preco.data_coleta else '',
                'fonte': preco.fonte
            })
        
        return JsonResponse({
            'success': True,
            'posto_id': posto_id,
            'precos': precos_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def detalhe_posto(request, posto_id):
    """Página de detalhes de um posto específico"""
    try:
        from .models import Estabelecimento, PrecoCombustivel
        
        posto = get_object_or_404(Estabelecimento, id=posto_id)
        precos = PrecoCombustivel.objects.filter(estabelecimento=posto).order_by('-data_coleta')
        
        precos_por_tipo = {}
        for preco in precos:
            if preco.tipo_combustivel not in precos_por_tipo:
                precos_por_tipo[preco.tipo_combustivel] = []
            precos_por_tipo[preco.tipo_combustivel].append(preco)
        
        TIPO_COMBUSTIVEL_DISPLAY = {
            'GASOLINA_COMUM': 'Gasolina Comum',
            'GASOLINA_ADITIVADA': 'Gasolina Aditivada',
            'ETANOL': 'Etanol',
            'DIESEL': 'Diesel',
            'DIESEL_S10': 'Diesel S10',
            'GNV': 'GNV',
        }
        
        context = {
            'posto': posto,
            'precos_por_tipo': precos_por_tipo,
            'TIPO_COMBUSTIVEL': TIPO_COMBUSTIVEL_DISPLAY,
            'total_precos': precos.count(),
        }
        
        return render(request, 'myapp/detalhe_posto.html', context)
        
    except Exception as e:
        print(f"⚠️ Erro ao carregar detalhes do posto {posto_id}: {e}")
        return HttpResponse(f"""
        <html>
        <head><title>Posto {posto_id}</title></head>
        <body>
            <h1>Posto {posto_id}</h1>
            <p>Erro ao carregar detalhes: {e}</p>
            <a href="/">Voltar para a página inicial</a>
        </body>
        </html>
        """)


def autocomplete_endereco(request):
    """Endpoint para autocomplete na busca de endereços"""
    from .models import Estabelecimento
    
    term = request.GET.get('term', '').strip().lower()
    
    if len(term) >= 2:
        suggestions = []
        
        try:
            # Busca cidades
            cidades = Estabelecimento.objects.filter(
                cidade__icontains=term
            ).values_list('cidade', flat=True).distinct()[:5]
            
            for cidade in cidades:
                suggestions.append({
                    'label': f'🏙️ {cidade} (cidade)',
                    'value': cidade,
                    'type': 'cidade'
                })
            
            # Busca bairros
            bairros = Estabelecimento.objects.filter(
                bairro__icontains=term
            ).values_list('bairro', flat=True).distinct()[:5]
            
            for bairro in bairros:
                suggestions.append({
                    'label': f'📍 {bairro} (bairro)',
                    'value': bairro,
                    'type': 'bairro'
                })
            
            # Busca endereços
            enderecos = Estabelecimento.objects.filter(
                endereco__icontains=term
            ).values_list('endereco', flat=True).distinct()[:5]
            
            for endereco in enderecos:
                endereco_short = endereco[:40] + ('...' if len(endereco) > 40 else '')
                suggestions.append({
                    'label': f'🏠 {endereco_short} (endereço)',
                    'value': endereco,
                    'type': 'endereco'
                })
            
            # Busca nome de postos
            postos = Estabelecimento.objects.filter(
                nome_fantasia__icontains=term
            ).values_list('nome_fantasia', flat=True).distinct()[:5]
            
            for posto in postos:
                suggestions.append({
                    'label': f'⛽ {posto} (posto)',
                    'value': posto,
                    'type': 'posto'
                })
            
        except Exception as e:
            print(f"⚠️ Erro no autocomplete: {e}")
        
        return JsonResponse(suggestions, safe=False)
    
    return JsonResponse([], safe=False)


def importar_excel(request):
    """Página para importação de dados via Excel"""
    
    context = {
        'arquivos_suportados': ['.xlsx', '.xls', '.csv'],
        'max_tamanho_mb': 10,
    }
    
    if request.method == 'POST' and request.FILES.get('arquivo'):
        try:
            arquivo = request.FILES['arquivo']
            nome_arquivo = arquivo.name
            
            if not nome_arquivo.lower().endswith(('.xlsx', '.xls', '.csv')):
                messages.error(request, '❌ Formato não suportado. Use .xlsx, .xls ou .csv.')
                return render(request, 'myapp/importar.html', context)
            
            if arquivo.size > 10 * 1024 * 1024:
                messages.error(request, '❌ Arquivo muito grande. Máximo 10MB.')
                return render(request, 'myapp/importar.html', context)
            
            if nome_arquivo.lower().endswith('.csv'):
                df = pd.read_csv(io.StringIO(arquivo.read().decode('utf-8')))
            else:
                df = pd.read_excel(arquivo)
            
            linhas_processadas = min(len(df), 100)
            context['dados_importados'] = {
                'linhas': len(df),
                'colunas': list(df.columns),
                'processadas': linhas_processadas,
                'amostra': df.head(3).to_dict('records') if len(df) > 0 else [],
            }
            
            messages.success(request, f'✅ Arquivo "{nome_arquivo}" processado com sucesso! {linhas_processadas} linhas importadas.')
            
        except Exception as e:
            messages.error(request, f'❌ Erro ao processar arquivo: {str(e)}')
    
    return render(request, 'myapp/importar.html', context)


def adicionar_precos_exemplo(request):
    """Adiciona preços de exemplo ao banco de dados"""
    from .models import Estabelecimento, PrecoCombustivel
    
    try:
        precos_base = {
            'Shell': {
                'GASOLINA_COMUM': 5.89, 
                'GASOLINA_ADITIVADA': 6.09, 
                'ETANOL': 4.29, 
                'DIESEL': 5.99,
                'DIESEL_S10': 6.19
            },
            'Ipiranga': {
                'GASOLINA_COMUM': 5.79, 
                'GASOLINA_ADITIVADA': 5.99, 
                'ETANOL': 4.19, 
                'DIESEL': 5.89
            },
            'BR': {
                'GASOLINA_COMUM': 5.75, 
                'GASOLINA_ADITIVADA': 5.95, 
                'ETANOL': 4.15, 
                'DIESEL': 5.85,
                'DIESEL_S10': 6.05
            },
            'Petrobras': {
                'GASOLINA_COMUM': 5.82, 
                'GASOLINA_ADITIVADA': 6.02, 
                'ETANOL': 4.22, 
                'DIESEL': 5.92
            },
            'Ale': {
                'GASOLINA_COMUM': 5.69, 
                'ETANOL': 4.09, 
                'DIESEL': 5.79
            }
        }
        
        estabelecimentos_sem_preco = Estabelecimento.objects.filter(precos__isnull=True)[:50]
        
        if not estabelecimentos_sem_preco:
            messages.info(request, '✅ Todos os estabelecimentos já têm preços cadastrados!')
            return redirect('index')
        
        total_precos_adicionados = 0
        
        for estabelecimento in estabelecimentos_sem_preco:
            bandeira = estabelecimento.bandeira or 'Ale'
            if bandeira not in precos_base:
                bandeira = 'Ale'
            
            precos_bandeira = precos_base[bandeira]
            
            tipos_disponiveis = list(precos_bandeira.keys())
            tipos_escolhidos = random.sample(
                tipos_disponiveis, 
                random.randint(2, min(4, len(tipos_disponiveis)))
            )
            
            for tipo_combustivel in tipos_escolhidos:
                variacao = random.uniform(0.97, 1.03)
                preco_base = precos_bandeira[tipo_combustivel]
                preco_final = round(preco_base * variacao, 3)
                
                PrecoCombustivel.objects.create(
                    estabelecimento=estabelecimento,
                    tipo_combustivel=tipo_combustivel,
                    preco=preco_final,
                    fonte='Sistema (dados exemplo)',
                    data_coleta=timezone.now()  # CORREÇÃO: Use timezone.now()
                )
                total_precos_adicionados += 1
        
        messages.success(
            request, 
            f'✅ {total_precos_adicionados} preços de exemplo adicionados para {len(estabelecimentos_sem_preco)} estabelecimentos!'
        )
        
    except Exception as e:
        messages.error(request, f'❌ Erro ao adicionar preços de exemplo: {str(e)}')
    
    return redirect('index')


def atualizar_precos_automatico(request):
    """Atualiza preços automaticamente"""
    from .models import Estabelecimento, PrecoCombustivel
    
    try:
        precos_referencia = {
            'GASOLINA_COMUM': 5.80,
            'GASOLINA_ADITIVADA': 6.00,
            'ETANOL': 4.10,
            'DIESEL': 5.90,
            'DIESEL_S10': 6.10,
            'GNV': 4.30
        }
        
        variacoes_bandeira = {
            'Shell': 1.05,
            'Ipiranga': 1.03,
            'BR': 1.02,
            'Petrobras': 1.04,
            'Ale': 0.98,
            'Raizen': 1.03,
            'Default': 1.00
        }
        
        uma_semana_atras = timezone.now() - timedelta(days=7)  # CORREÇÃO: Use timezone.now()
        postos_para_atualizar = Estabelecimento.objects.filter(
            precos__data_coleta__lt=uma_semana_atras
        ).distinct()[:100]
        
        if not postos_para_atualizar:
            messages.info(request, '✅ Todos os preços estão atualizados (menos de 7 dias)!')
            return redirect('index')
        
        total_atualizados = 0
        postos_processados = 0
        
        for posto in postos_para_atualizar:
            postos_processados += 1
            
            bandeira = posto.bandeira or 'Default'
            fator_bandeira = variacoes_bandeira.get(bandeira, variacoes_bandeira['Default'])
            
            tipos_combustivel_posto = set(
                posto.precos.values_list('tipo_combustivel', flat=True).distinct()
            )
            
            for tipo_combustivel in tipos_combustivel_posto:
                if tipo_combustivel in precos_referencia:
                    preco_base = precos_referencia[tipo_combustivel]
                    variacao_aleatoria = random.uniform(0.98, 1.02)
                    novo_preco = round(preco_base * fator_bandeira * variacao_aleatoria, 3)
                    
                    PrecoCombustivel.objects.create(
                        estabelecimento=posto,
                        tipo_combustivel=tipo_combustivel,
                        preco=novo_preco,
                        fonte='Atualização Automática',
                        data_coleta=timezone.now()  # CORREÇÃO: Use timezone.now()
                    )
                    total_atualizados += 1
        
        messages.success(
            request, 
            f'✅ {total_atualizados} preços atualizados automaticamente para {postos_processados} postos!'
        )
        
    except Exception as e:
        messages.error(request, f'❌ Erro na atualização automática: {str(e)}')
    
    return redirect('index')


# NOVAS VIEWS PARA SCRAPING (simplificadas)

def scraping_precos(request):
    """Interface para executar scraping de preços"""
    from .models import PrecoCombustivel
    
    resultado = None
    if request.method == 'POST':
        # Aqui você implementaria o scraping real
        # Por enquanto, apenas simula
        resultado = {
            'sucesso': True,
            'atualizados': 0,
            'novos_postos': 0,
            'data_hora': timezone.now(),
            'mensagem': 'Scraping simulado (implemente a lógica real)'
        }
        messages.info(request, '⚠️ Funcionalidade de scraping ainda não implementada completamente.')
    
    context = {
        'resultado': resultado,
        'ultima_atualizacao': PrecoCombustivel.objects.order_by('-data_coleta').first().data_coleta if PrecoCombustivel.objects.exists() else None,
    }
    
    return render(request, 'myapp/scraping.html', context)


def api_scraping_precos(request):
    """API para executar scraping"""
    return JsonResponse({
        'sucesso': False,
        'erro': 'Funcionalidade ainda não implementada',
        'data_hora': timezone.now().isoformat()
    })


def dashboard_scraping(request):
    """Dashboard para monitoramento do scraping"""
   
    
    try:
        from .models import Estabelecimento, PrecoCombustivel
        
        total_postos = Estabelecimento.objects.count()
        total_precos = PrecoCombustivel.objects.count()
        postos_sem_precos = Estabelecimento.objects.filter(precos__isnull=True).count()
        ultimos_precos = PrecoCombustivel.objects.order_by('-data_coleta')[:10]
        
        context = {
            'total_postos': total_postos,
            'total_precos': total_precos,
            'postos_sem_precos': postos_sem_precos,
            'ultimos_precos': ultimos_precos,
            'atualizacoes_por_fonte': PrecoCombustivel.objects.values('fonte').annotate(
                total=Count('id')
            ).order_by('-total'),
        }
        
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        context = {
            'total_postos': 0,
            'total_precos': 0,
            'postos_sem_precos': 0,
            'ultimos_precos': [],
            'atualizacoes_por_fonte': [],
        }
    
    return render(request, 'myapp/dashboard_scraping.html', context)


# API VIEWS (simplificadas)

def api_lista_postos(request):
    """API para listar postos (JSON)"""
    try:
        from .models import Estabelecimento
        postos = Estabelecimento.objects.all()[:50]
        
        data = []
        for posto in postos:
            data.append({
                'id': posto.id,
                'nome': posto.nome_fantasia,
                'cidade': posto.cidade,
                'uf': posto.uf,
                'bandeira': posto.bandeira,
                'endereco': posto.endereco,
                'latitude': posto.latitude,
                'longitude': posto.longitude,
                'url_detalhes': f'/posto/{posto.id}/'
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'postos': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def api_detalhe_posto(request, posto_id):
    """API para detalhes de um posto específico (JSON)"""
    try:
        from .models import Estabelecimento, PrecoCombustivel
        
        posto = get_object_or_404(Estabelecimento, id=posto_id)
        
        precos = PrecoCombustivel.objects.filter(
            estabelecimento=posto
        ).order_by('-data_coleta')
        
        precos_data = []
        for preco in precos[:10]:
            precos_data.append({
                'tipo': preco.tipo_combustivel,
                'preco': float(preco.preco),
                'data': preco.data_coleta.strftime('%d/%m/%Y %H:%M') if preco.data_coleta else '',
                'fonte': preco.fonte
            })
        
        data = {
            'id': posto.id,
            'nome': posto.nome_fantasia,
            'razao_social': posto.razao_social,
            'cnpj': posto.cnpj,
            'endereco': posto.endereco,
            'bairro': posto.bairro,
            'cidade': posto.cidade,
            'uf': posto.uf,
            'cep': posto.cep,
            'bandeira': posto.bandeira,
            'latitude': posto.latitude,
            'longitude': posto.longitude,
            'telefone': posto.telefone,
            'precos': precos_data,
            'total_precos': precos.count()
        }
        
        return JsonResponse({
            'success': True,
            'posto': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
def debug_postos(request):
    """View para debug dos dados dos postos"""
    from .models import Estabelecimento
    
    postos = Estabelecimento.objects.all()[:10]
    
    debug_info = []
    for posto in postos:
        debug_info.append({
            'id': posto.id,
            'nome': posto.nome_fantasia,
            'latitude': posto.latitude,
            'longitude': posto.longitude,
            'tem_coordenadas': bool(posto.latitude and posto.longitude),
            'cidade': posto.cidade,
            'bandeira': posto.bandeira,
        })
    
    return JsonResponse({
        'total_postos': Estabelecimento.objects.count(),
        'postos_com_coordenadas': Estabelecimento.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        ).count(),
        'amostra': debug_info
    })
    
def debug_coordenadas(request):
    """View para debug de coordenadas dos postos"""
    from .models import Estabelecimento
    import json
    
    # Verifica todos os postos
    todos_postos = Estabelecimento.objects.all()
    
    debug_data = []
    for posto in todos_postos[:50]:  # Primeiros 50
        debug_data.append({
            'id': posto.id,
            'nome': posto.nome_fantasia,
            'latitude_raw': posto.latitude,
            'longitude_raw': posto.longitude,
            'latitude_float': None,
            'longitude_float': None,
            'convertido': False,
            'cidade': posto.cidade,
            'bandeira': posto.bandeira,
        })
    
    # Tenta converter para float
    for data in debug_data:
        try:
            data['latitude_float'] = float(data['latitude_raw']) if data['latitude_raw'] else None
            data['longitude_float'] = float(data['longitude_raw']) if data['longitude_raw'] else None
            data['convertido'] = data['latitude_float'] is not None and data['longitude_float'] is not None
        except:
            data['convertido'] = False
    
    return render(request, 'myapp/debug_coordenadas.html', {
        'postos': debug_data,
        'total_postos': todos_postos.count(),
    })