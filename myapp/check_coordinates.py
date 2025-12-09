# myapp/management/commands/check_coordinates.py
from django.core.management.base import BaseCommand
from myapp.models import Estabelecimento

class Command(BaseCommand):
    help = 'Verifica postos sem coordenadas'
    
    def handle(self, *args, **kwargs):
        total = Estabelecimento.objects.count()
        com_coordenadas = Estabelecimento.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        ).exclude(latitude=0, longitude=0).count()
        
        self.stdout.write(f'Total de postos: {total}')
        self.stdout.write(f'Postos com coordenadas: {com_coordenadas}')
        self.stdout.write(f'Postos SEM coordenadas: {total - com_coordenadas}')
        
        # Mostra alguns exemplos
        sem_coordenadas = Estabelecimento.objects.filter(
            latitude__isnull=True
        )[:5]
        
        for posto in sem_coordenadas:
            self.stdout.write(f'  - {posto.nome_fantasia} ({posto.cidade}-{posto.uf})')