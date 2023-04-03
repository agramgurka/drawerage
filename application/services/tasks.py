import random
import re

import requests

from ..models import Language, Task


class Restriction:
    values = ()


class IdRestriction(Restriction):
    def __init__(self, *, ids):
        self.values = ids


class TextRestriction(Restriction):
    def __init__(self, *, phrases):
        self.values = phrases


class BaseTaskProvider:
    LANGUAGES = ()

    def __init__(self, lang: Language) -> None:
        if self.LANGUAGES and lang.code not in self.LANGUAGES:
            raise ValueError(f'{lang} is not supported in {self.__class__}')
        self.language = lang
        self.setup()
        self.check_self()

    def setup(self):
        pass

    def check_self(self):
        pass

    def get_task(self, restrictions=()) -> tuple[Task, list[Restriction]]:
        raise NotImplementedError()


class PredefinedTaskProvider(BaseTaskProvider):
    def check_self(self):
        if not Task.objects.filter(language=self.language, auto_created=False).exists():
            raise ValueError('No tasks exist in DB')

    def get_task(self, restrictions=None) -> tuple[Task, list[Restriction]]:
        if not restrictions:
            restrictions = []

        qs = Task.objects.filter(language=self.language, auto_created=False)
        items = []
        other_restrictions = []
        for r in restrictions:
            if isinstance(r, IdRestriction):
                items.extend(r.values)
            else:
                other_restrictions.append(r)
        if items:
            qs = qs.exclude(id__in=items)

        task = qs.order_by('?')[0]
        return (
            task,
            other_restrictions + [IdRestriction(ids=list(set(items) | {task.id}))],
        )


class ExternalTextTaskProvider(BaseTaskProvider):
    SOURCE = None

    choices = ()

    def get_source(self):
        assert self.SOURCE, 'SOURCE for ExternalTextTaskProvider must be defined'
        return self.SOURCE

    def check_self(self):
        if not self.choices:
            raise ValueError('Provider doesn\'t contain task variants')

    def get_task(self, restrictions=None) -> tuple[Task, list[Restriction]]:
        if not restrictions:
            restrictions = []

        other_restrictions = []
        items = []
        for r in restrictions:
            if isinstance(r, TextRestriction):
                items.extend(r.values)
            else:
                other_restrictions.append(r)

        task_text = None

        num_of_saved_tasks = Task.objects.filter(auto_created=True, source=self.SOURCE).count()
        total_tasks = len(self.choices) or num_of_saved_tasks * 5  # default is 20% choice item is in DB

        # from DB or from generator
        db_rate = num_of_saved_tasks / (total_tasks or 1)

        # assume there are more choices than players
        attempts = len(self.choices)
        while task_text is None and attempts > 0:
            probability_of_fetch_from_db = random.random()
            if probability_of_fetch_from_db >= db_rate:
                try_text = random.choice(self.choices)
            else:
                try_text = Task.objects.filter(
                    auto_created=True,
                    source=self.get_source(),
                    # TODO: need to fetch it smartly, looking at the rate
                ).order_by('?').first().text

            stored_task = Task.objects.filter(
                auto_created=True,
                text__iexact=task_text,
            ).first()

            if stored_task:
                # We want to have a probability to show even disliked tasks
                should_display_probability = random.random()
                should_display = (stored_task.up_vote + 1) / (stored_task.down_vote + 1) > should_display_probability
            else:
                should_display = True
            if try_text not in items and should_display:
                task_text = try_text
            attempts -= 1

        if task_text is None:
            raise ValueError('Can\'t create unique task')

        # find existing tasks
        task = Task.objects.filter(
            auto_created=True,
            text__iexact=task_text,
        ).first() or Task(
            language=self.language,
            auto_created=True,
            text=task_text,
            source=self.get_source(),
        )

        return (
            task,
            other_restrictions + [TextRestriction(phrases=list(set(items) | {task_text}))]
        )


class RuslangTaskProvider(ExternalTextTaskProvider):
    LANGUAGES = ('ru',)
    URL = 'http://dict.ruslang.ru/magn.php?act=search'
    SOURCE = 'ruslang_phrases'

    def setup(self):
        response = requests.get(self.URL)
        self.choices = re.findall(r'<span.*?>(.*?)</span>', response.text)


class RuslangTaskSingleNounProvider(ExternalTextTaskProvider):
    LANGUAGES = ('ru',)
    URL = 'http://dict.ruslang.ru/freq.php?act=show&dic=freq_s'
    SOURCE = 'ruslang_nouns'

    def setup(self):
        response = requests.get(self.URL)
        self.choices = re.findall(
            r'<tr><td.*?<td>(.*?)</td>.*?</tr>',
            response.text
        )


class AcademicoupWordTaskProvider(ExternalTextTaskProvider):
    LANGUAGES = ('en',)
    URL = 'https://academic.oup.com/view-large/1188011'
    SOURCE = 'academic_oup'

    def setup(self):
        response = requests.get(
            self.URL,
            headers={
                'User-agent': (
                    'Mozilla/5.0 (Linux; Android 10; SM-G996U Build/QP1A.190711.020; wv) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36'
                ),
            },
        )
        self.choices = list(set(re.findall(
            r'<tr><td>\d+\.\s*(.*?)\..</td></tr>',
            response.text
        )))
