# cron_scraping.py
import os
import django
import sys

# Adiciona o diretório do projeto ao path
sys.path.append('/caminho/para/seu/projeto')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.scraping import FuelPriceScraper

def executar_scraping():
    print("🔄 Executando scraping agendado...")
    
    scraper = FuelPriceScraper()
    resultado = scraper.atualizar_precos_do_scraping()
    
    print(f"✅ Scraping concluído: {resultado}")
    
    # Log do resultado
    with open('/caminho/para/logs/scraping.log', 'a') as f:
        f.write(f"{datetime.now()}: {resultado}\n")
    
    return resultado

if __name__ == "__main__":
    executar_scraping()