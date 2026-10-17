from django.core.management.base import BaseCommand

from aa_moonregistry.utils import refresh_sovereignty

class Command(BaseCommand):
    help = 'Does initial load of all system sovereignty'

    def handle(self, *args, **kwargs):
        
        refresh_sovereignty()