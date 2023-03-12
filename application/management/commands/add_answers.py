import logging

from django.core.management import BaseCommand

from ...models import AutoAnswer, Language


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            default='chatgpt',
            help='Source of the task'
        )
        parser.add_argument(
            '--lang',
            default='ru',
            help='Language 2-letters code'
        )

    def handle(self, source, lang, *args, **options):
        self.stdout.write("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.\n")
        contents = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            contents.append(line)

        language = Language.objects.get(code=lang)
        for line in contents:
            line = line.strip('\r\n .,!')
            if not line:
                continue
            try:
                AutoAnswer.objects.create(language=language, text=line, source=source)
            except Exception:
                logging.getLogger(__name__).exception('Problem with saving Task model occured')
