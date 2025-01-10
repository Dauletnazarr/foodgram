import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импортирует ингредиенты из CSV файла'

    def handle(self, *args, **kwargs):
        # Захардкоженный путь к файлу
        csv_file_path = '../data/ingredients.csv'

        ingredients_to_create = []

        try:
            # Открытие CSV файла
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    # Если строка состоит из двух
                    # элементов (название, единица измерения)
                    if len(row) == 2:
                        name = row[0].strip()
                        measurement_unit = row[1].strip()

                        # Добавление объектов в список
                        ingredients_to_create.append(Ingredient(
                            name=name,
                            measurement_unit=measurement_unit
                        ))

                    else:
                        self.stdout.write(self.style.WARNING(
                            f'Пропущена строка с неверным форматом: {row}'))

            if ingredients_to_create:
                # bulk_create для добавления всех ингредиентов за один запрос
                Ingredient.objects.bulk_create(ingredients_to_create,
                                               ignore_conflicts=True)
                self.stdout.write(
                    self.style.SUCCESS('Ингредиенты успешно добавлены.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'Файл {csv_file_path} не найден.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Произошла ошибка: {str(e)}'))
