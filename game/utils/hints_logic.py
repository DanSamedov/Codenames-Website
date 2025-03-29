from game.models import Hint 


def add_hint(game, team, hint_word, hint_num):
    hint_obj, created = Hint.objects.get_or_create(game=game)

    hint_obj.hints[team].append({"word": hint_word, "num": hint_num})

    hint_obj.save()


def get_last_hint(game):
    hint_obj = Hint.objects.filter(game=game).first()
    if hint_obj:
        all_hints = [hint for hints in hint_obj.hints.values() for hint in hints]
        if all_hints:
            return all_hints[-1]
    return None
