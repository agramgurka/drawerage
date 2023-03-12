from ..models import AutoAnswer, Language


def get_auto_answers(lang: Language, number: int = 1) -> list[str]:
    if number < 1:
        return []
    return list(
        AutoAnswer.objects.filter(language=lang).order_by('?').values_list('text', flat=True)[:number]
    )
