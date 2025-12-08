# myapp/views.py - VERSÃO CORRIGIDA
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
    """View para exibir mapa de postos"""
    try:
        from .models import Estabelecimento, PrecoCombustivel
        
        estabelecimentos = Estabelecimento.objects.all()
        
        postos_data = []
        for estabelecimento in estabelecimentos:
            precos_dict = {}
            try:
                precos = PrecoCombustivel.objects.filter(estabelecimento=estabelecimento)
                for preco in precos:
                    precos_dict[preco.tipo_combustivel] = str(preco.preco)
            except Exception as e:
                print(f"Erro ao buscar preços para {estabelecimento.id}: {e}")
            
            lat = estabelecimento.latitude if estabelecimento.latitude else -15.7797
            lng = estabelecimento.longitude if estabelecimento.longitude else -47.9297
            
            postos_data.append({
                'id': estabelecimento.id,
                'nome': estabelecimento.nome_fantasia or estabelecimento.razao_social or 'Posto',
                'endereco': estabelecimento.endereco or '',
                'cidade': estabelecimento.cidade or '',
                'uf': estabelecimento.uf or '',
                'latitude': float(lat),
                'longitude': float(lng),
                'bandeira': estabelecimento.bandeira or '',
                'precos': precos_dict
            })
        
        bandeiras = Estabelecimento.objects.exclude(
            bandeira__isnull=True
        ).exclude(
            bandeira__exact=''
        ).values_list('bandeira', flat=True).distinct().order_by('bandeira')
        
        context = {
            'postos': estabelecimentos,
            'postos_json': json.dumps(postos_data, ensure_ascii=False),
            'total_postos': estabelecimentos.count(),
            'bandeiras': bandeiras,
        }
        
    except Exception as e:
        print(f"⚠️ Erro na view mapa_postos: {e}")
        context = {
            'postos': [],
            'postos_json': '[]',
            'total_postos': 0,
            'bandeiras': [],
        }
    
    return render(request, 'myapp/mapa.html', context)


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
    from django.db.models import Count
    
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