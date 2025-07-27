import logging
from django.db import transaction
from room.models import Game
from game.models import Card
from game.utils.hints_logic import add_hint
from .constants import TEAM_RED, TEAM_BLUE, TEAM_DRAW
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GameEventProcessor:
    def __init__(self, game_id: Any) -> None:
        self.game_id = game_id
        logger.debug(f"GameEventProcessor initialized for game_id={game_id}")

    def save_submitted_hints(self, data: Dict) -> None:
        if not data:
            logger.warning(f"save_submitted_hints called with empty data for game_id={self.game_id}")
            return

        logger.info(f"Saving submitted hint for game_id={self.game_id}: {data}")
        with transaction.atomic():
            game = Game.objects.get(id=self.game_id)
            add_hint(
                game,
                data["leaderTeam"],
                data["hintWord"],
                data["hintNum"]
            )
            logger.debug("Hint successfully saved.")

    def save_picked_words(self, data: Dict) -> Optional[Dict[str, Any]]:
        if not data:
            logger.warning(f"save_picked_words called with empty data for game_id={self.game_id}")
            return None

        logger.info(f"Saving picked words for game_id={self.game_id}: {data}")
        with transaction.atomic():
            game = Game.objects.get(pk=self.game_id)
            picked_words = data["pickedCards"]
            team = data["team"]

            logger.debug(f"Checking for assassin among picked words: {picked_words}")
            potential_assassin = Card.objects.filter(
                game=game,
                word__in=picked_words,
                color='Black'
            ).first()

            if potential_assassin:
                logger.info(f"Assassin card picked: {potential_assassin.word} by team {team}")
                Card.objects.filter(pk=potential_assassin.pk).update(is_guessed=True)

                winner = team
                game.winners = winner
                game.save(update_fields=['winners'])
                logger.debug(f"Game over due to assassin pick. Winner: {winner}")
                return self.game_over_payload(winner=winner, reason="assassin_picked", game=game)

            picked_cards = Card.objects.filter(
                game=game,
                word__in=picked_words
            )
            picked_cards.update(is_guessed=True)
            logger.debug(f"Marked picked cards as guessed: {[c.word for c in picked_cards]}")

            instant_win_payload = self.check_instant_win(game)
            if instant_win_payload:
                logger.debug("Game over due to instant win condition.")
                return instant_win_payload

            logger.debug("No game-ending condition met.")
            return None

    def check_instant_win(self, game: Any) -> Optional[Dict[str, Any]]:
        with transaction.atomic():
            red_guesses, blue_guesses, starting_team = game.tally_scores()
            logger.debug(f"Tally scores - Red: {red_guesses}, Blue: {blue_guesses}, Starting: {starting_team}")

            red_wins  = (starting_team == TEAM_RED and red_guesses >= 9) or (starting_team != TEAM_RED and red_guesses >= 8)
            blue_wins = (starting_team == TEAM_BLUE and blue_guesses >= 9) or (starting_team != TEAM_BLUE and blue_guesses >= 8)

            if red_wins and blue_wins:
                logger.info("Both teams met winning condition simultaneously. Declaring a draw.")
                game.winners = TEAM_DRAW
                game.save(update_fields=['winners'])
                return self.game_over_payload(winner=TEAM_DRAW, reason="all_cards_guessed", game=game)

            elif red_wins or blue_wins:
                winner = TEAM_RED if red_wins else TEAM_BLUE
                logger.info(f"Instant win detected. Winner: {winner}")
                game.winners = winner
                game.save(update_fields=['winners'])
                return self.game_over_payload(winner=winner, reason="all_cards_guessed", game=game)

            logger.debug("No team has met the instant win condition.")
            return None

    def game_over_payload(self, winner: str, reason: str, game: Any) -> Dict[str, Any]:
        logger.debug(f"Generating game over payload. Winner: {winner}, Reason: {reason}")
        return {
            "winner": winner,
            "reason": reason,
            "red_score": game.red_team_score,
            "blue_score": game.blue_team_score
        }
