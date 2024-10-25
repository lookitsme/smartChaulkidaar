from django.core.management.base import BaseCommand
from main_app.models import GuardLocation

class Command(BaseCommand):
    help = 'Clears all guard location records from the database'

    def handle(self, *args, **kwargs):
        GuardLocation.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared all guard location records'))
