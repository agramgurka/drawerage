from typing import Any

from ..models import Task


class Restriction:
    values = ()


class IdRestriction(Restriction):
    def __init__(self, *, ids):
        self.values = ids


class TextRestriction(Restriction):
    def __init__(self, *, sentences):
        self.values = sentences


class BaseTaskProducer:
    def get_task(self, restrictions=()) -> tuple[str, Any]:
        raise NotImplementedError()


class PredefinedTaskProducer(BaseTaskProducer):
    def get_task(self, restrictions=None):
        if not restrictions:
            restrictions = []

        qs = Task.objects.filter(language='ru')
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
