import csv
import os

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from recipes.models import Ingredient


class Command(BaseCommand):

    def handle(self, *args, **options):
        if Ingredient.objects.exists():
            self.stdout.write(self.style.WARNING('Данные загружены'))
            return None
        try:
            self.load_data(path=os.path.join('data', 'ingredients.csv'))
        except Exception as err:
            self.stdout.write(
                self.style.ERROR(f'Error: {err}'))
        else:
            self.stdout.write(self.style.SUCCESS('Данные добавлены'))

    @staticmethod
    def load_data(path):
        with open(path, encoding='UTF-8') as f:
            reader = csv.reader(f)
            next(reader)
            try:
                Ingredient.objects.bulk_create(
                    [Ingredient(name=name, measurement_unit=measurement_unit)
                     for name, measurement_unit in reader])
            except IntegrityError:
                pass
