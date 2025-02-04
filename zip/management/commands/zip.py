import csv
from django.core.management.base import BaseCommand
from zip.models import Location

class Command(BaseCommand):
    help = 'Import locations from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file to be imported')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                country, district, zip_code = row
                Location.objects.get_or_create(country=country, district=district, zip_code=zip_code)
                self.stdout.write(self.style.SUCCESS(f'Successfully imported {country} - {district} - {zip_code}'))
