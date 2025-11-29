from django.shortcuts import render
from django.db.models import Q  
from django.contrib import messages
from django.http import JsonResponse
from .models import Estabelecimento, PrecoCombustivel  # ADICIONE PrecoCombustivel
import pandas as pd
import random  # ADICIONE esta importação

def index(request):
    return render(request, 'myapp/index.html')

def pesquisar(request):
    query = request.GET.get('q', '')
    tipo_pesquisa = request.GET.get('tipo', 'nome')
    resultados = []

    if query:
        if tipo_pesquisa == 'cnpj':
            # Remove pontuação do CNPJ para busca
            cnpj_limpo = ''.join(filter(str.isdigit, query))
            resultados = Estabelecimento.objects.filter(
                cnpj__icontains=cnpj_limpo
            ).prefetch_related('precos')  # ADICIONE ESTA LINHA
        
        elif tipo_pesquisa == 'cidade':
            uf = request.GET.get('uf', '')
            if uf:
                resultados = Estabelecimento.objects.filter(
                    Q(cidade__icontains=query) & Q(uf__iexact=uf)
                ).prefetch_related('precos')  # ADICIONE ESTA LINHA
            else:
                resultados = Estabelecimento.objects.filter(
                    cidade__icontains=query
                ).prefetch_related('precos')  # ADICIONE ESTA LINHA
        
        elif tipo_pesquisa == 'bandeira':
            resultados = Estabelecimento.objects.filter(
                bandeira__icontains=query
            ).prefetch_related('precos')  # ADICIONE ESTA LINHA
        
        else:  # Pesquisa por nome (padrão)
            resultados = Estabelecimento.objects.filter(
                Q(nome_fantasia__icontains=query) |
                Q(razao_social__icontains=query) |
                Q(cidade__icontains=query) |
                Q(bairro__icontains=query) |
                Q(endereco__icontains=query)
            ).prefetch_related('precos')  # ADICIONE ESTA LINHA

    return render(request, 'myapp/pesquisar.html', {
        'resultados': resultados,
        'query': query,
        'tipo_pesquisa': tipo_pesquisa
    })

def lista_estabelecimentos(request):
    estabelecimentos = Estabelecimento.objects.all()
    return render(request, 'myapp/lista.html', {
        'estabelecimentos': estabelecimentos
    })
    
def importar_excel(request):
    if request.method == 'POST' and request.FILES.get('arquivo_excel'):
        arquivo = request.FILES['arquivo_excel']
        
        try:
            # Verifica a extensão do arquivo para escolher o engine correto
            if arquivo.name.endswith('.xlsb'):
                # Lê arquivo Excel Binário (.xlsb)
                df = pd.read_excel(arquivo, engine='pyxlsb')
            elif arquivo.name.endswith('.xlsx') or arquivo.name.endswith('.xls'):
                # Lê arquivos Excel normais (.xlsx, .xls)
                df = pd.read_excel(arquivo)
            else:
                messages.error(request, '❌ Formato de arquivo não suportado. Use .xlsx, .xls ou .xlsb.')
                return render(request, 'myapp/importar.html')
            
            print(f"📊 Iniciando importação de {len(df)} registros...")
            
            total_importados = 0
            total_erros = 0
            estabelecimentos_batch = []
            
            for index, row in df.iterrows():
                try:
                    # Prepara os dados conforme sua planilha
                    cnpj = str(row['CNPJ']).strip() if pd.notna(row['CNPJ']) else ''
                    razao_social = str(row['RAZAO_SOCIAL']).strip()[:200] if pd.notna(row['RAZAO_SOCIAL']) else ''
                    endereco = str(row['ENDERECO']).strip()[:300] if pd.notna(row['ENDERECO']) else ''
                    municipio = str(row['MUNICIPIO']).strip()[:100] if pd.notna(row['MUNICIPIO']) else ''
                    uf = str(row['UF']).strip()[:2] if pd.notna(row['UF']) else ''
                    bandeira = str(row['BANDEIRA']).strip()[:100] if pd.notna(row['BANDEIRA']) else ''
                    
                    # Usa a razão social como nome fantasia (já que não tem coluna separada)
                    nome_fantasia = razao_social[:200]
                    
                    # Cria o objeto
                    estabelecimento = Estabelecimento(
                        cnpj=cnpj,
                        razao_social=razao_social,
                        nome_fantasia=nome_fantasia,
                        bandeira=bandeira,
                        endereco=endereco,
                        bairro='',  # Não tem na planilha
                        cidade=municipio,  # MUNICIPIO vira cidade
                        uf=uf,
                        cep=''  # Não tem na planilha
                    )
                    
                    estabelecimentos_batch.append(estabelecimento)
                    
                    # Salva em lotes de 500 para melhor performance
                    if len(estabelecimentos_batch) >= 500:
                        Estabelecimento.objects.bulk_create(estabelecimentos_batch, ignore_conflicts=True)
                        total_importados += len(estabelecimentos_batch)
                        estabelecimentos_batch = []
                        print(f"✅ Lote importado: {total_importados} registros")
                    
                except Exception as e:
                    total_erros += 1
                    if total_erros <= 5:  # Mostra apenas os primeiros 5 erros
                        print(f"❌ Erro na linha {index}: {e}")
                    continue
            
            # Salva os registros restantes
            if estabelecimentos_batch:
                Estabelecimento.objects.bulk_create(estabelecimentos_batch, ignore_conflicts=True)
                total_importados += len(estabelecimentos_batch)
            
            print(f"🎉 Importação finalizada: {total_importados} importados, {total_erros} erros")
            messages.success(request, f'✅ Importação concluída! {total_importados} registros importados, {total_erros} erros.')
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            messages.error(request, f'❌ Erro ao importar arquivo: {str(e)}')
    
    return render(request, 'myapp/importar.html')


# ========== NOVAS FUNÇÕES PARA PREÇOS DE COMBUSTÍVEL ==========

def adicionar_precos_exemplo(request):
    """Adiciona preços de exemplo para os estabelecimentos"""
    try:
        # Preços de exemplo baseados em bandeiras
        precos_exemplo = {
            'Shell': {'GASOLINA_COMUM': 5.89, 'GASOLINA_ADITIVADA': 6.09, 'ETANOL': 4.29, 'DIESEL': 5.99},
            'Ipiranga': {'GASOLINA_COMUM': 5.79, 'GASOLINA_ADITIVADA': 5.99, 'ETANOL': 4.19, 'DIESEL': 5.89},
            'BR': {'GASOLINA_COMUM': 5.75, 'GASOLINA_ADITIVADA': 5.95, 'DIESEL': 5.85, 'DIESEL_S10': 6.05},
            'Ale': {'GASOLINA_COMUM': 5.69, 'ETANOL': 4.09, 'DIESEL': 5.79},
            'Petrobras': {'GASOLINA_COMUM': 5.82, 'GASOLINA_ADITIVADA': 6.02, 'ETANOL': 4.22, 'DIESEL': 5.92},
        }
        
        # Adiciona preços para os primeiros 100 estabelecimentos
        estabelecimentos = Estabelecimento.objects.all()[:100]
        total_precos = 0
        
        for estabelecimento in estabelecimentos:
            bandeira = estabelecimento.bandeira or 'Shell'
            precos_bandeira = precos_exemplo.get(bandeira, precos_exemplo['Shell'])
            
            # Adiciona variação de +/- 5% nos preços
            for tipo_combustivel, preco_base in precos_bandeira.items():
                variacao = random.uniform(0.95, 1.05)  # +/- 5%
                preco_final = round(preco_base * variacao, 2)
                
                PrecoCombustivel.objects.create(
                    estabelecimento=estabelecimento,
                    tipo_combustivel=tipo_combustivel,
                    preco=preco_final,
                    fonte='Sistema (exemplo)'
                )
                total_precos += 1
        
        messages.success(request, f'✅ {total_precos} preços de exemplo adicionados para {len(estabelecimentos)} estabelecimentos!')
    
    except Exception as e:
        messages.error(request, f'❌ Erro ao adicionar preços: {str(e)}')
    
    return render(request, 'myapp/index.html')

def buscar_precos_anp(request, cnpj):
    """Busca preços da ANP (simulação) para um estabelecimento específico"""
    try:
        estabelecimento = Estabelecimento.objects.get(cnpj=cnpj)
        
        # Preços simulados baseados na bandeira
        precos_simulados = {
            'Shell': {'GASOLINA_COMUM': 5.89, 'GASOLINA_ADITIVADA': 6.09, 'ETANOL': 4.29},
            'Ipiranga': {'GASOLINA_COMUM': 5.79, 'GASOLINA_ADITIVADA': 5.99, 'ETANOL': 4.19},
            'BR': {'GASOLINA_COMUM': 5.75, 'GASOLINA_ADITIVADA': 5.95, 'DIESEL': 5.45},
            'Ale': {'GASOLINA_COMUM': 5.69, 'ETANOL': 4.09, 'DIESEL': 5.39},
        }
        
        bandeira = estabelecimento.bandeira or 'Shell'
        precos = precos_simulados.get(bandeira, precos_simulados['Shell'])
        
        # Salva os preços no banco
        for tipo, valor in precos.items():
            PrecoCombustivel.objects.create(
                estabelecimento=estabelecimento,
                tipo_combustivel=tipo,
                preco=valor,
                fonte='ANP (simulado)'
            )
        
        return JsonResponse({'status': 'success', 'precos': precos})
    
    except Estabelecimento.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Estabelecimento não encontrado'})
    
def atualizar_precos_automatico(request):
    """Atualiza preços automaticamente para todos os estabelecimentos"""
    from django.utils import timezone
    import random
    
    try:
        # Preços base atualizados
        precos_base = {
            'Shell': {'GASOLINA_COMUM': 5.89, 'GASOLINA_ADITIVADA': 6.09, 'ETANOL': 4.29, 'DIESEL': 5.99},
            'Ipiranga': {'GASOLINA_COMUM': 5.79, 'GASOLINA_ADITIVADA': 5.99, 'ETANOL': 4.19, 'DIESEL': 5.89},
            'BR': {'GASOLINA_COMUM': 5.75, 'GASOLINA_ADITIVADA': 5.95, 'ETANOL': 4.15, 'DIESEL': 5.85},
            'Ale': {'GASOLINA_COMUM': 5.69, 'GASOLINA_ADITIVADA': 5.89, 'ETANOL': 4.09, 'DIESEL': 5.79},
            'Petrobras': {'GASOLINA_COMUM': 5.82, 'GASOLINA_ADITIVADA': 6.02, 'ETANOL': 4.22, 'DIESEL': 5.92},
        }
        
        estabelecimentos_sem_preco = Estabelecimento.objects.filter(precos__isnull=True)
        total_adicionados = 0
        
        print(f"🔄 Atualizando preços para {estabelecimentos_sem_preco.count()} estabelecimentos sem preços...")
        
        for estabelecimento in estabelecimentos_sem_preco[:1000]:  # Limita a 1000 por vez
            bandeira = estabelecimento.bandeira or 'Shell'
            precos_bandeira = precos_base.get(bandeira, precos_base['Shell'])
            
            # Adiciona 2-3 tipos de combustível
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
        messages.error(request, f'❌ Erro ao atualizar preços: {str(e)}')
    
    return render(request, 'myapp/index.html')