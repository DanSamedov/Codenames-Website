from game.models import Hint 
from typing import Any, Optional


def add_hint(game: Any, team: str, hint_word: str, hint_num: int) -> Any:    
    return Hint.objects.create(
        game=game,
        team=team,
        word=hint_word,
        num=hint_num
    )


def get_last_hint(game_id: Any) -> Optional[Any]:
    try:
        return Hint.objects.filter(
            game_id=game_id, 
        ).latest('created_at')
    except Hint.DoesNotExist:
        return None
