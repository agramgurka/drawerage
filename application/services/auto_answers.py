from ..models import AutoAnswer


def get_auto_answers(lang: str, number: int = 1) -> list[str]:
    if number < 1:
        return []
    return list(
        AutoAnswer.objects.filter(language=lang).order_by('?').values_list('text', flat=True)[:number]
    )
