from game.models import Hint 


def add_hint(game, team, hint_word, hint_num):
    hint_obj, created = Hint.objects.get_or_create(game=game)

    hint_obj.hints[team].append({"word": hint_word, "num": hint_num})

    hint_obj.save()


def get_last_hint(game, team):
    hint_obj = Hint.objects.filter(game=game).first()
    if hint_obj and team in hint_obj.hints and hint_obj.hints[team]:
        return hint_obj.hints[team][-1]
    return None
