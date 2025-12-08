# myapp/scraping.py
import requests
import time
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
from django.utils import timezone
from .models import Estabelecimento, PrecoCombustivel

class FuelPriceScraper:
    """Classe responsável por buscar preços de combustíveis na web"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_postos_posto(self, cidade="São Paulo", uf="SP"):
        """Busca preços no site Postos.Posto.com.br"""
        try:
            # URL base do site (exemplo)
            base_url = f"https://postos.posto.com.br/precos/{cidade.lower().replace(' ', '-')}-{uf.lower()}"
            
            print(f"🔍 Buscando preços em {base_url}")
            
            # Em um scraper real, você faria a requisição HTTP:
            # response = self.session.get(base_url, timeout=10)
            # soup = BeautifulSoup(response.text, 'html.parser')
            
            # Simulação de dados (remova quando implementar o scraping real)
            simulated_data = self._simulate_postos_posto_data(cidade, uf)
            
            return simulated_data
            
        except Exception as e:
            print(f"❌ Erro ao buscar preços no Postos.Posto: {e}")
            return []
    
    def scrape_precos_combustiveis(self, estado="SP"):
        """Busca preços médios por estado"""
        try:
            # API de preços médios (exemplo)
            api_url = f"https://precoscombustiveis.com.br/api/precos-medios/{estado}"
            
            # Em um scraper real:
            # response = self.session.get(api_url, timeout=10)
            # data = response.json()
            
            # Simulação
            simulated_data = self._simulate_precos_combustiveis_data(estado)
            
            return simulated_data
            
        except Exception as e:
            print(f"❌ Erro ao buscar preços médios: {e}")
            return {}
    
    def scrape_google_maps(self, localizacao, raio_km=10):
        """Busca postos no Google Maps"""
        try:
            # Nota: O Google Maps requer API Key e tem limitações
            # Esta é uma implementação simplificada
            
            lat, lng = localizacao
            api_key = "SUA_API_KEY_AQUI"  # Você precisa de uma API Key do Google
            
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': raio_km * 1000,
                'type': 'gas_station',
                'key': api_key,
                'language': 'pt-BR'
            }
            
            # Em produção:
            # response = self.session.get(url, params=params, timeout=10)
            # data = response.json()
            
            # Simulação
            simulated_data = self._simulate_google_maps_data(localizacao, raio_km)
            
            return simulated_data
            
        except Exception as e:
            print(f"❌ Erro ao buscar no Google Maps: {e}")
            return []
    
    def _simulate_postos_posto_data(self, cidade, uf):
        """Simula dados do Postos.Posto (para teste)"""
        print(f"📊 Simulando dados para {cidade}/{uf}")
        
        postos = []
        bandeiras = ['Shell', 'Ipiranga', 'BR', 'Petrobras', 'Ale', 'Raizen']
        
        for i in range(10):
            posto = {
                'nome': f'Posto {bandeiras[i % len(bandeiras)]} {i+1}',
                'endereco': f'Rua Exemplo {i+1}, Bairro Centro',
                'cidade': cidade,
                'uf': uf,
                'bandeira': bandeiras[i % len(bandeiras)],
                'precos': {
                    'GASOLINA_COMUM': round(5.80 + random.uniform(-0.20, 0.30), 3),
                    'GASOLINA_ADITIVADA': round(6.00 + random.uniform(-0.20, 0.30), 3),
                    'ETANOL': round(4.10 + random.uniform(-0.15, 0.20), 3),
                    'DIESEL': round(5.90 + random.uniform(-0.20, 0.30), 3),
                }
            }
            postos.append(posto)
        
        return postos
    
    def _simulate_precos_combustiveis_data(self, estado):
        """Simula dados de preços médios"""
        precos_base = {
            'SP': {
                'GASOLINA_COMUM': 5.80,
                'GASOLINA_ADITIVADA': 6.00,
                'ETANOL': 4.10,
                'DIESEL': 5.90,
                'DIESEL_S10': 6.10,
            },
            'RJ': {
                'GASOLINA_COMUM': 5.90,
                'GASOLINA_ADITIVADA': 6.10,
                'ETANOL': 4.20,
                'DIESEL': 6.00,
                'DIESEL_S10': 6.20,
            },
            'MG': {
                'GASOLINA_COMUM': 5.75,
                'GASOLINA_ADITIVADA': 5.95,
                'ETANOL': 4.05,
                'DIESEL': 5.85,
                'DIESEL_S10': 6.05,
            },
            'PR': {
                'GASOLINA_COMUM': 5.70,
                'GASOLINA_ADITIVADA': 5.90,
                'ETANOL': 4.00,
                'DIESEL': 5.80,
                'DIESEL_S10': 6.00,
            },
        }
        
        return precos_base.get(estado, precos_base['SP'])
    
    def _simulate_google_maps_data(self, localizacao, raio_km):
        """Simula dados do Google Maps"""
        lat, lng = localizacao
        postos = []
        
        for i in range(5):
            # Gera coordenadas aleatórias dentro do raio
            offset_lat = random.uniform(-0.01, 0.01) * raio_km
            offset_lng = random.uniform(-0.01, 0.01) * raio_km
            
            posto = {
                'nome': f'Posto Google {i+1}',
                'endereco': f'Rua Virtual {i+1}',
                'latitude': lat + offset_lat,
                'longitude': lng + offset_lng,
                'precos': {
                    'GASOLINA_COMUM': round(5.80 + random.uniform(-0.10, 0.20), 3),
                    'ETANOL': round(4.10 + random.uniform(-0.10, 0.15), 3),
                }
            }
            postos.append(posto)
        
        return postos
    
    def atualizar_precos_do_scraping(self):
        """Atualiza preços no banco com base no scraping"""
        try:
            print("🔄 Iniciando atualização de preços via scraping...")
            
            total_atualizados = 0
            total_novos_postos = 0
            
            # 1. Busca preços por cidade/estado
            estados = Estabelecimento.objects.values_list('uf', flat=True).distinct()
            
            for estado in estados[:3]:  # Limita a 3 estados por execução
                print(f"📍 Buscando preços para o estado {estado}...")
                
                # Busca preços médios do estado
                precos_estado = self.scrape_precos_combustiveis(estado)
                
                if precos_estado:
                    # Atualiza postos deste estado
                    postos_estado = Estabelecimento.objects.filter(uf=estado)[:20]  # Limita a 20 postos
                    
                    for posto in postos_estado:
                        atualizou = self._atualizar_posto_com_precos_estado(posto, precos_estado)
                        if atualizou:
                            total_atualizados += 1
                
                # Pequena pausa para não sobrecarregar servidores
                time.sleep(2)
            
            # 2. Busca postos específicos por cidade
            cidades_principais = Estabelecimento.objects.values_list('cidade', 'uf').distinct()[:5]
            
            for cidade, uf in cidades_principais:
                print(f"🏙️ Buscando postos em {cidade}/{uf}...")
                
                postos_scraped = self.scrape_postos_posto(cidade, uf)
                
                for posto_data in postos_scraped:
                    criado = self._criar_ou_atualizar_posto(posto_data)
                    if criado == 'criado':
                        total_novos_postos += 1
                    elif criado == 'atualizado':
                        total_atualizados += 1
                
                time.sleep(3)
            
            print(f"✅ Scraping concluído: {total_atualizados} preços atualizados, {total_novos_postos} novos postos")
            
            return {
                'sucesso': True,
                'atualizados': total_atualizados,
                'novos_postos': total_novos_postos,
                'data_hora': timezone.now()
            }
            
        except Exception as e:
            print(f"❌ Erro no scraping: {e}")
            return {
                'sucesso': False,
                'erro': str(e),
                'data_hora': timezone.now()
            }
    
    def _atualizar_posto_com_precos_estado(self, posto, precos_estado):
        """Atualiza preços de um posto com base nos preços do estado"""
        try:
            atualizou = False
            
            for tipo_combustivel, preco_medio in precos_estado.items():
                # Adiciona variação baseada na bandeira
                variacao_bandeira = self._get_variacao_por_bandeira(posto.bandeira)
                preco_final = round(preco_medio * variacao_bandeira, 3)
                
                # Adiciona pequena variação aleatória
                variacao_aleatoria = random.uniform(0.97, 1.03)
                preco_final = round(preco_final * variacao_aleatoria, 3)
                
                # Cria novo registro de preço
                PrecoCombustivel.objects.create(
                    estabelecimento=posto,
                    tipo_combustivel=tipo_combustivel,
                    preco=preco_final,
                    fonte='Scraping Web',
                    data_coleta=timezone.now()
                )
                
                atualizou = True
            
            return atualizou
            
        except Exception as e:
            print(f"Erro ao atualizar posto {posto.id}: {e}")
            return False
    
    def _criar_ou_atualizar_posto(self, posto_data):
        """Cria ou atualiza um posto com dados do scraping"""
        try:
            # Verifica se o posto já existe (por nome e cidade)
            postos_existentes = Estabelecimento.objects.filter(
                nome_fantasia__icontains=posto_data['nome'],
                cidade=posto_data['cidade'],
                uf=posto_data['uf']
            )
            
            if postos_existentes.exists():
                # Atualiza posto existente
                posto = postos_existentes.first()
                
                # Atualiza preços
                for tipo_combustivel, preco in posto_data.get('precos', {}).items():
                    PrecoCombustivel.objects.create(
                        estabelecimento=posto,
                        tipo_combustivel=tipo_combustivel,
                        preco=preco,
                        fonte='Scraping Web - Postos.Posto',
                        data_coleta=timezone.now()
                    )
                
                return 'atualizado'
            
            else:
                # Cria novo posto
                novo_posto = Estabelecimento.objects.create(
                    nome_fantasia=posto_data['nome'],
                    razao_social=posto_data['nome'],
                    endereco=posto_data.get('endereco', ''),
                    bairro=posto_data.get('bairro', ''),
                    cidade=posto_data['cidade'],
                    uf=posto_data['uf'],
                    bandeira=posto_data.get('bandeira', ''),
                    latitude=posto_data.get('latitude'),
                    longitude=posto_data.get('longitude'),
                )
                
                # Adiciona preços
                for tipo_combustivel, preco in posto_data.get('precos', {}).items():
                    PrecoCombustivel.objects.create(
                        estabelecimento=novo_posto,
                        tipo_combustivel=tipo_combustivel,
                        preco=preco,
                        fonte='Scraping Web - Postos.Posto',
                        data_coleta=timezone.now()
                    )
                
                return 'criado'
                
        except Exception as e:
            print(f"Erro ao criar/atualizar posto: {e}")
            return 'erro'
    
    def _get_variacao_por_bandeira(self, bandeira):
        """Retorna fator de variação baseado na bandeira"""
        variacoes = {
            'Shell': 1.05,      # +5%
            'Ipiranga': 1.03,   # +3%
            'BR': 1.02,         # +2%
            'Petrobras': 1.04,  # +4%
            'Raizen': 1.03,     # +3%
            'Ale': 0.98,        # -2%
        }
        return variacoes.get(bandeira, 1.00)