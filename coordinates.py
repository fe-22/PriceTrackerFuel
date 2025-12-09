# generate_coordinates.py (coloque na raiz do projeto)
import os
import sys
import django
import random
from datetime import datetime

# Configura o Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.models import Estabelecimento

def generate_coordinates_for_all():
    """Gera coordenadas para TODOS os postos sem coordenadas"""
    
    print("🚀 Iniciando geração de coordenadas...")
    print(f"Hora: {datetime.now()}")
    
    # Conta total de postos
    total_postos = Estabelecimento.objects.count()
    print(f"Total de postos no banco: {total_postos}")
    
    # Postos sem coordenadas
    postos_sem_coords = Estabelecimento.objects.filter(
        latitude__isnull=True,
        longitude__isnull=True
    )
    
    print(f"Postos SEM coordenadas: {postos_sem_coords.count()}")
    
    if postos_sem_coords.count() == 0:
        print("✅ Todos os postos já têm coordenadas!")
        return
    
    # Dicionário de coordenadas por estado
    coordenadas_por_estado = {
        'SP': [(-23.5505, -46.6333), (-22.9068, -43.1729), (-23.1791, -45.8872)],  # SP, RJ, Taubaté
        'RJ': [(-22.9068, -43.1729), (-22.7642, -43.3505)],  # RJ, Niterói
        'MG': [(-19.9167, -43.9345), (-21.7594, -43.3505)],  # BH, Juiz de Fora
        'RS': [(-30.0277, -51.2287), (-29.1686, -51.1794)],  # POA, Caxias do Sul
        'PR': [(-25.4284, -49.2733), (-23.3105, -51.1628)],  # Curitiba, Londrina
        'SC': [(-27.5954, -48.5480), (-26.3051, -48.8461)],  # Florianópolis, Joinville
        'DF': [(-15.7797, -47.9297)],  # Brasília
        'BA': [(-12.9704, -38.5124), (-14.7969, -39.1733)],  # Salvador, Ilhéus
        'PE': [(-8.0476, -34.8770), (-8.2833, -35.9764)],  # Recife, Caruaru
        'CE': [(-3.7319, -38.5267), (-4.9342, -37.9727)],  # Fortaleza, Aracati
        'GO': [(-16.6869, -49.2648), (-18.1667, -48.1667)],  # Goiânia, Itumbiara
        'MT': [(-15.6011, -56.0974), (-16.4700, -54.6356)],  # Cuiabá, Rondonópolis
        'MS': [(-20.4428, -54.6464), (-22.2215, -54.8064)],  # Campo Grande, Dourados
        'ES': [(-20.3155, -40.3128), (-19.5189, -40.4069)],  # Vitória, Colatina
        'PA': [(-1.4558, -48.4902), (-2.4429, -54.7045)],  # Belém, Santarém
        'AM': [(-3.1190, -60.0217), (-2.5299, -60.0232)],  # Manaus, Itacoatiara
        'AC': [(-9.9747, -67.8100), (-10.9384, -68.6577)],  # Rio Branco, Cruzeiro do Sul
        'AL': [(-9.6658, -35.7350), (-9.3932, -37.9988)],  # Maceió, Arapiraca
        'AP': [(0.0349, -51.0694), (3.8416, -51.8345)],  # Macapá, Oiapoque
        'MA': [(-2.5391, -44.2829), (-5.0892, -42.8016)],  # São Luís, Teresina
        'PB': [(-7.1195, -34.8450), (-7.2306, -35.8811)],  # João Pessoa, Campina Grande
        'PI': [(-5.0892, -42.8016), (-7.0764, -41.4710)],  # Teresina, Picos
        'RN': [(-5.7945, -35.2110), (-6.0351, -37.2740)],  # Natal, Mossoró
        'RO': [(-8.7612, -63.9039), (-11.7439, -61.7725)],  # Porto Velho, Ji-Paraná
        'RR': [(2.8223, -60.6758), (3.3602, -60.8226)],  # Boa Vista, Caracaraí
        'SE': [(-10.9472, -37.0731), (-11.2617, -37.4386)],  # Aracaju, Estância
        'TO': [(-10.1844, -48.3336), (-9.5354, -48.0932)],  # Palmas, Araguaína
    }
    
    # Processa os postos
    atualizados = 0
    batch_size = 50  # Processa em lotes para não sobrecarregar
    
    for i, posto in enumerate(postos_sem_coords, 1):
        try:
            # Determina UF (estado)
            uf = posto.uf.strip().upper() if posto.uf else 'SP'
            
            # Pega coordenadas base para o estado
            if uf in coordenadas_por_estado:
                base_coords = random.choice(coordenadas_por_estado[uf])
            else:
                # Fallback: coordenadas no centro do Brasil
                base_coords = (-15.7797, -47.9297)  # Brasília
            
            # Adiciona variação aleatória
            lat_base, lng_base = base_coords
            lat = lat_base + random.uniform(-0.3, 0.3)  # Variação de ~33km
            lng = lng_base + random.uniform(-0.3, 0.3)
            
            # Garante que está dentro do Brasil
            lat = max(min(lat, 5.0), -35.0)  # Norte ao Sul do Brasil
            lng = max(min(lng, -30.0), -75.0)  # Leste a Oeste do Brasil
            
            # Atualiza o posto
            posto.latitude = round(lat, 6)
            posto.longitude = round(lng, 6)
            posto.save()
            
            atualizados += 1
            
            # Progresso a cada 50 postos
            if i % 50 == 0:
                print(f"  Processados: {i}/{postos_sem_coords.count()}")
            
            # Mostra os primeiros 5
            if i <= 5:
                print(f"  ✅ {posto.nome_fantasia[:30]}...: {lat:.6f}, {lng:.6f} ({uf})")
        
        except Exception as e:
            print(f"  ⚠️ Erro no posto {posto.id}: {e}")
            continue
    
    print(f"\n🎉 CONCLUSÃO:")
    print(f"   Postos atualizados: {atualizados}")
    print(f"   Hora final: {datetime.now()}")
    
    # Verifica resultado
    total_com_coords = Estabelecimento.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).exclude(latitude=0, longitude=0).count()
    
    print(f"   Total com coordenadas agora: {total_com_coords}/{total_postos}")
    
    if total_com_coords > 0:
        print("✅ PRONTO! Agora o mapa deve mostrar os postos.")
    else:
        print("❌ Algo deu errado. Nenhuma coordenada foi gerada.")

if __name__ == "__main__":
    generate_coordinates_for_all()