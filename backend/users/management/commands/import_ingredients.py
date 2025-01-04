import csv
from users.models import Ingredient
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Импортирует ингредиенты из CSV файла'

    def add_arguments(self, parser):
        # Определение аргументов командной строки
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу для импорта')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        try:
            # Открытие CSV файла
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) == 2:  # Если строка состоит из двух элементов (название, единица измерения)
                        name = row[0].strip()
                        measurement_unit = row[1].strip()
                        # Создание объекта Ingredient и сохранение в базе данных
                        Ingredient.objects.get_or_create(name=name, measurement_unit=measurement_unit)
                        self.stdout.write(self.style.SUCCESS(f'Ингредиент {name} успешно добавлен.'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Пропущена строка с неверным форматом: {row}'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл {csv_file_path} не найден.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Произошла ошибка: {str(e)}'))
