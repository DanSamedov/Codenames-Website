import os
from django.core.management.base import BaseCommand
from game.models import Word

class Command(BaseCommand):
    help = 'Load words from data/words.txt into the database'

    def handle(self, *args, **kwargs):
        words_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data',
            'words.txt'
        )

        if not os.path.exists(words_file_path):
            self.stderr.write(self.style.ERROR(f"Words file not found: {words_file_path}"))
            return

        with open(words_file_path, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]

        added_count = 0
        for word_text in words:
            word_obj, created = Word.objects.get_or_create(text=word_text)
            if created:
                added_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {added_count} new words.'))
