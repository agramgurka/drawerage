from typing import Any
import re
import random

import requests

from ..models import Task


class Restriction:
    values = ()


class IdRestriction(Restriction):
    def __init__(self, *, ids):
        self.values = ids


class TextRestriction(Restriction):
    def __init__(self, *, phrases):
        self.values = phrases


class BaseTaskProducer:
    LANGUAGES = ()

    def __init__(self, lang: str) -> None:
        if self.LANGUAGES and lang not in self.LANGUAGES:
            raise NotImplementedError(f'{lang} is not supported in {self.__class__}')
        self.language = lang

    def get_task(self, restrictions=()) -> tuple[str, Any]:
        raise NotImplementedError()


class PredefinedTaskProducer(BaseTaskProducer):
    def get_task(self, restrictions=None):
        if not restrictions:
            restrictions = []

        qs = Task.objects.filter(language=self.language)
        items = []
        other_restrictions = []
        for r in restrictions:
            if isinstance(r, IdRestriction):
                items.extend(r.values)
            else:
                other_restrictions.append(r)
        if items:
            qs = qs.exclude(id__in=items)

        task = qs.order_by('?').first()
        return task.text.lower().strip(), other_restrictions + [IdRestriction(ids=list(set(items) | {task.id}))]


class RuslangTaskProducer(BaseTaskProducer):
    LANGUAGES = ('ru',)
    URL = 'http://dict.ruslang.ru/magn.php?act=search'

    def __init__(self, lang: str):
        super().__init__(lang)
        response = requests.get(self.URL)
        self.choices = re.findall(r'<span.*?>(.*?)</span>', response.text)

    def get_task(self, restrictions=None) -> tuple[str, Any]:
        if not restrictions:
            restrictions = []

        task = random.choice(self.choices)
        other_restrictions = []
        items = []
        for r in restrictions:
            if isinstance(r, TextRestriction):
                items.extend(r.values)
            else:
                other_restrictions.append(r)

        return task.lower().strip(), other_restrictions + [TextRestriction(phrases=list(set(items) | {task}))]
