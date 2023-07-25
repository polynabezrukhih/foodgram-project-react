import os

from django.core.management.base import BaseCommand
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_path = (settings.BASE_DIR.parent, 'data', 'ingredients.csv')
