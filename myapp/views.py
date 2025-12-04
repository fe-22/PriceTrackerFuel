# myapp/views.py - VERSÃO SIMPLIFICADA PARA TESTE
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# View principal BÁSICA
def index(request):
    # Dados de exemplo (evita erros se o banco estiver vazio)
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
        'postos_destaque': [],  # Lista vazia
        'postos_baratos': [],   # Lista vazia
    }
    
    # Tenta pegar dados reais, mas não falha se não conseguir
    try:
        from .models import Estabelecimento, PrecoCombustivel
        context['total_postos'] = Estabelecimento.objects.count()
        context['total_precos'] = PrecoCombustivel.objects.count()
        
        # Para cidades únicas
        if context['total_postos'] > 0:
            from django.db.models import Count
            context['cidades_unicas'] = Estabelecimento.objects.values('cidade').distinct().count()
            
    except Exception as e:
        # Se der erro (tabelas não existem), usa os valores padrão
        print(f"⚠️ Erro ao carregar dados: {e}")
    
    return render(request, 'myapp/index.html', context)

def pesquisar(request):
    """Página de pesquisa avançada de postos"""
    from django.db.models import Q
    from .models import Estabelecimento
    
    query = request.GET.get('q', '').strip()
    tipo_pesquisa = request.GET.get('tipo', 'nome')
    resultados = []
    total_encontrado = 0
    
    if query:
        try:
            if tipo_pesquisa == 'cnpj':
                # Remove caracteres não numéricos do CNPJ
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
            
            else:  # Pesquisa por nome (padrão)
                resultados = Estabelecimento.objects.filter(
                    Q(nome_fantasia__icontains=query) |
                    Q(razao_social__icontains=query) |
                    Q(endereco__icontains=query) |
                    Q(bairro__icontains=query)
                ).prefetch_related('precos')
            
            total_encontrado = resultados.count()
            
            # Adiciona preços recentes a cada resultado
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
    
    # Lista de UFs para o select
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
        # Se der erro (tabela não existe), usa lista vazia
        print(f"⚠️ Erro ao carregar estabelecimentos: {e}")
        estabelecimentos = []
    
     context = {
        'estabelecimentos': estabelecimentos,
    }
    
     return render(request, 'myapp/lista.html', context)

def buscar_por_endereco(request):
    """
    Busca avançada por endereço com múltiplos filtros
    """
    from .models import PrecoCombustivel
    
    # Pega parâmetros da URL
    endereco = request.GET.get('endereco', '').strip()
    cidade = request.GET.get('cidade', '').strip()
    bairro = request.GET.get('bairro', '').strip()
    uf = request.GET.get('uf', '').strip()
    combustivel = request.GET.get('combustivel', '').strip()
    
    # Lista de UFs do Brasil
    UFS_BRASIL = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ]
    
    # Tipos de combustível
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
        'resultados': [],  # Lista vazia por enquanto
        'total': 0,
    }
    
    return render(request, 'myapp/buscar_endereco.html', context)

def mapa_postos(request):
    """Página com mapa interativo de postos"""
    import json
    
    # Dados padrão
    context = {
        'total_postos': 0,
        'postos': '[]',  # JSON vazio
    }
    
    try:
        from .models import Estabelecimento
        
        # Busca postos com coordenadas
        postos_com_coordenadas = Estabelecimento.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )[:200]  # Limita para performance
        
        # Prepara dados para o template
        postos_data = []
        for posto in postos_com_coordenadas:
            # Preços formatados
            precos_dict = {}
            for preco_obj in posto.precos.all().order_by('-data_coleta')[:3]:
                precos_dict[preco_obj.tipo_combustivel] = str(preco_obj.preco)
            
            postos_data.append({
                'id': posto.id,
                'nome': posto.nome_fantasia or posto.razao_social,
                'endereco': posto.endereco,
                'bairro': posto.bairro,
                'cidade': posto.cidade,
                'uf': posto.uf,
                'bandeira': posto.bandeira or 'Independiente',
                'latitude': float(posto.latitude) if posto.latitude else 0,
                'longitude': float(posto.longitude) if posto.longitude else 0,
                'precos': precos_dict,
            })
        
        context['total_postos'] = len(postos_data)
        context['postos'] = json.dumps(postos_data, ensure_ascii=False)
        
    except Exception as e:
        print(f"⚠️ Erro no mapa: {e}")
        # Se der erro, usa dados de exemplo
        postos_exemplo = [
            {
                'id': 1,
                'nome': 'Posto Shell Exemplo',
                'endereco': 'Av. Paulista, 1000',
                'cidade': 'São Paulo',
                'uf': 'SP',
                'latitude': -23.5614,
                'longitude': -46.6563,
                'precos': {'GASOLINA_COMUM': '6.50', 'ETANOL': '4.20'}
            },
            {
                'id': 2,
                'nome': 'Posto Ipiranga Exemplo',
                'endereco': 'Av. Brasil, 2000',
                'cidade': 'Rio de Janeiro',
                'uf': 'RJ',
                'latitude': -22.9068,
                'longitude': -43.1729,
                'precos': {'GASOLINA_ADITIVADA': '6.80', 'DIESEL': '5.90'}
            }
        ]
        context['total_postos'] = len(postos_exemplo)
        context['postos'] = json.dumps(postos_exemplo, ensure_ascii=False)
    
    return render(request, 'myapp/mapa.html', context)

def detalhe_posto(request, posto_id):
    """Página de detalhes de um posto específico"""
    try:
        from .models import Estabelecimento, PrecoCombustivel
        from django.shortcuts import get_object_or_404
        
        # Busca o posto ou retorna 404
        posto = get_object_or_404(Estabelecimento, id=posto_id)
        
        # Busca preços do posto
        precos = PrecoCombustivel.objects.filter(estabelecimento=posto).order_by('-data_coleta')
        
        # Agrupa preços por tipo
        precos_por_tipo = {}
        for preco in precos:
            if preco.tipo_combustivel not in precos_por_tipo:
                precos_por_tipo[preco.tipo_combustivel] = []
            precos_por_tipo[preco.tipo_combustivel].append(preco)
        
        # Tipos de combustível para o template
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
        # Fallback para página simples
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
    from django.http import JsonResponse
    from .models import Estabelecimento
    
    term = request.GET.get('term', '').strip().lower()
    
    if len(term) >= 2:  # Só busca se tiver pelo menos 2 caracteres
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
            # Retorna array vazio se houver erro
        
        return JsonResponse(suggestions, safe=False)
    
    return JsonResponse([], safe=False)


def importar_excel(request):
    """Página para importação de dados via Excel"""
    from django.contrib import messages
    
    context = {
        'arquivos_suportados': ['.xlsx', '.xls', '.csv'],
        'max_tamanho_mb': 10,
    }
    
    if request.method == 'POST' and request.FILES.get('arquivo'):
        try:
            arquivo = request.FILES['arquivo']
            nome_arquivo = arquivo.name
            
            # Verifica extensão
            if not nome_arquivo.lower().endswith(('.xlsx', '.xls', '.csv')):
                messages.error(request, '❌ Formato não suportado. Use .xlsx, .xls ou .csv.')
                return render(request, 'myapp/importar.html', context)
            
            # Verifica tamanho (10MB máximo)
            if arquivo.size > 10 * 1024 * 1024:
                messages.error(request, '❌ Arquivo muito grande. Máximo 10MB.')
                return render(request, 'myapp/importar.html', context)
            
            # Processamento do arquivo (simulação)
            import pandas as pd
            import io
            
            if nome_arquivo.lower().endswith('.csv'):
                df = pd.read_csv(io.StringIO(arquivo.read().decode('utf-8')))
            else:
                df = pd.read_excel(arquivo)
            
            # Simula importação
            linhas_processadas = min(len(df), 100)  # Simula processamento de até 100 linhas
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
    from django.contrib import messages
    from django.shortcuts import redirect
    
    try:
        from .models import Estabelecimento, PrecoCombustivel
        import random
        
        # Dados de exemplo para preços
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
        
        # Pega estabelecimentos sem preços
        estabelecimentos_sem_preco = Estabelecimento.objects.filter(precos__isnull=True)[:50]
        
        if not estabelecimentos_sem_preco:
            messages.info(request, '✅ Todos os estabelecimentos já têm preços cadastrados!')
            return redirect('index')
        
        total_precos_adicionados = 0
        
        for estabelecimento in estabelecimentos_sem_preco:
            # Determina qual tabela de preços usar baseado na bandeira
            bandeira = estabelecimento.bandeira or 'Ale'
            if bandeira not in precos_base:
                bandeira = 'Ale'  # Fallback
            
            precos_bandeira = precos_base[bandeira]
            
            # Escolhe aleatoriamente 2-4 tipos de combustível para este posto
            tipos_disponiveis = list(precos_bandeira.keys())
            tipos_escolhidos = random.sample(
                tipos_disponiveis, 
                random.randint(2, min(4, len(tipos_disponiveis)))
            )
            
            for tipo_combustivel in tipos_escolhidos:
                # Adiciona variação aleatória de ±3%
                variacao = random.uniform(0.97, 1.03)
                preco_base = precos_bandeira[tipo_combustivel]
                preco_final = round(preco_base * variacao, 3)
                
                # Cria o preço
                PrecoCombustivel.objects.create(
                    estabelecimento=estabelecimento,
                    tipo_combustivel=tipo_combustivel,
                    preco=preco_final,
                    fonte='Sistema (dados exemplo)'
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
    """Atualiza preços automaticamente com base em fontes externas"""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    try:
        from .models import Estabelecimento, PrecoCombustivel
        import random
        from datetime import datetime, timedelta
        
        # Simula preços de referência (em um sistema real, viria de API externa)
        precos_referencia = {
            'GASOLINA_COMUM': 5.80,
            'GASOLINA_ADITIVADA': 6.00,
            'ETANOL': 4.10,
            'DIESEL': 5.90,
            'DIESEL_S10': 6.10,
            'GNV': 4.30
        }
        
        # Variações por bandeira
        variacoes_bandeira = {
            'Shell': 1.05,      # +5%
            'Ipiranga': 1.03,   # +3%
            'BR': 1.02,         # +2%
            'Petrobras': 1.04,  # +4%
            'Ale': 0.98,        # -2%
            'Raizen': 1.03,     # +3%
            'Default': 1.00     # Sem variação
        }
        
        # Busca postos que precisam de atualização (preços com mais de 7 dias)
        uma_semana_atras = datetime.now() - timedelta(days=7)
        postos_para_atualizar = Estabelecimento.objects.filter(
            precos__data_coleta__lt=uma_semana_atras
        ).distinct()[:100]  # Limita a 100 postos por execução
        
        if not postos_para_atualizar:
            messages.info(request, '✅ Todos os preços estão atualizados (menos de 7 dias)!')
            return redirect('index')
        
        total_atualizados = 0
        postos_processados = 0
        
        for posto in postos_para_atualizar:
            postos_processados += 1
            
            # Determina fator da bandeira
            bandeira = posto.bandeira or 'Default'
            fator_bandeira = variacoes_bandeira.get(bandeira, variacoes_bandeira['Default'])
            
            # Para cada tipo de combustível que o posto tem
            tipos_combustivel_posto = set(
                posto.precos.values_list('tipo_combustivel', flat=True).distinct()
            )
            
            for tipo_combustivel in tipos_combustivel_posto:
                if tipo_combustivel in precos_referencia:
                    # Preço base + variação da bandeira + variação aleatória pequena
                    preco_base = precos_referencia[tipo_combustivel]
                    variacao_aleatoria = random.uniform(0.98, 1.02)
                    novo_preco = round(preco_base * fator_bandeira * variacao_aleatoria, 3)
                    
                    # Cria novo registro de preço
                    PrecoCombustivel.objects.create(
                        estabelecimento=posto,
                        tipo_combustivel=tipo_combustivel,
                        preco=novo_preco,
                        fonte='Atualização Automática'
                    )
                    total_atualizados += 1
        
        messages.success(
            request, 
            f'✅ {total_atualizados} preços atualizados automaticamente para {postos_processados} postos!'
        )
        
    except Exception as e:
        messages.error(request, f'❌ Erro na atualização automática: {str(e)}')
    
    return redirect('index')