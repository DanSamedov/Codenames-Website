import time
import threading
from dataclasses import dataclass, field
from django.core.cache import cache
import logging
from room.models import Game
from .constants import PHASE_HINT, PHASE_ROUND, TEAM_RED, TEAM_BLUE, HINT_PHASE_DURATION, ROUND_PHASE_DURATION, PHASE_CACHE_TIMEOUT_BUFFER
from typing import Any, Callable, Optional, Dict

logger = logging.getLogger(__name__)


@dataclass
class Phase:
    name: str
    duration: int
    team: str
    start_time: float = field(default_factory=time.time)
    _transition_thread: Optional[threading.Thread] = None

    def time_remaining(self) -> float:
        remaining = max(0, (self.start_time + self.duration) - time.time())
        logger.debug(f"Time remaining for phase '{self.name}': {remaining:.2f} seconds")
        return remaining

    def schedule_transition(self, callback: Callable[["Phase"], None]) -> None:
        def transition_task():
            remaining = self.time_remaining()
            if remaining > 0:
                logger.info(f"Phase '{self.name}' sleeping for {remaining:.2f} seconds before transitioning")
                time.sleep(remaining)
            logger.info(f"Executing transition for phase '{self.name}'")
            try:
                callback(self)
            except Exception as e:
                logger.exception(f"Exception in phase transition callback: {e}")

        if self._transition_thread is not None and self._transition_thread.is_alive():
            logger.debug(f"Transition thread for phase '{self.name}' is already running")
            return

        logger.debug(f"Starting transition thread for phase '{self.name}'")
        self._transition_thread = threading.Thread(target=transition_task, daemon=True)
        self._transition_thread.start()

    def serialize(self) -> Dict[str, Any]:
        return {
            "phase": self.name,
            "duration": self.duration,
            "team": self.team,
            "start_time": self.start_time,
        }


class PhaseManager:
    def __init__(self, game_id: Any, channel_layer: Any, game_group_name: str, event_sender: Any, event_processor: Any, cache_selected_cards: str) -> None:
        self.game_id = game_id
        self.cache_prefix = f"game_{self.game_id}"
        self.channel_layer = channel_layer
        self.game_group_name = game_group_name
        self.event_sender = event_sender
        self.event_processor = event_processor
        self.current_phase = None
        self.cache_selected_cards = cache_selected_cards
        logger.debug(f"PhaseManager initialized for game {self.game_id}")

    def set_phase(self, phase_name: str, duration: int, team: str) -> Phase:
        logger.info(f"Setting new phase: {phase_name} | Duration: {duration} | Team: {team}")
        self.current_phase = Phase(name=phase_name, duration=duration, team=team)
        cache.set(f"{self.cache_prefix}_phase", self.current_phase.serialize(), timeout=duration + PHASE_CACHE_TIMEOUT_BUFFER)
        return self.current_phase

    def get_phase(self) -> Optional[Phase]:
        phase_data = cache.get(f"{self.cache_prefix}_phase")
        if not phase_data:
            logger.warning(f"No phase found in cache for game {self.game_id}")
            self.current_phase = None
            return None

        if (
            not self.current_phase
            or self.current_phase.name != phase_data['phase']
            or self.current_phase.team != phase_data['team']
            or self.current_phase.start_time != phase_data['start_time']
        ):
            logger.debug("Phase data in cache differs from current_phase, reinitializing")
            self.current_phase = Phase(
                name=phase_data['phase'],
                duration=phase_data['duration'],
                team=phase_data['team'],
                start_time=phase_data['start_time'],
            )

        return self.current_phase

    @property
    def selected_cards(self) -> Any:
        cards = cache.get(self.cache_selected_cards, [])
        logger.debug(f"Retrieved selected cards for game {self.game_id}: {cards}")
        return cards

    @selected_cards.setter
    def selected_cards(self, value: Any) -> None:
        logger.debug(f"Setting selected cards for game {self.game_id}: {value}")
        cache.set(self.cache_selected_cards, value, timeout=None)

    def _on_phase_expire(self, phase: Phase) -> None:
        logger.info(f"Phase expired: {phase.name} (Team: {phase.team})")

        try:
            game = Game.objects.get(pk=self.game_id)
            if game.winners:
                logger.info(f"Game {self.game_id} already has a winner. Skipping phase transition.")
                return
        except Game.DoesNotExist:
            logger.error(f"Game with ID {self.game_id} not found during phase expiration.")
            return

        current = self.get_phase()
        if not current or current.name != phase.name or current.start_time != phase.start_time or current.team != phase.team:
            logger.info("Phase mismatch or stale transition, aborting transition.")
            return

        self.selected_cards = []
        next_team = TEAM_RED if phase.team == TEAM_BLUE else TEAM_BLUE

        if phase.name == PHASE_HINT:
            logger.info("Transitioning from hint_phase to round_phase")
            self.set_phase(phase_name=PHASE_ROUND, duration=ROUND_PHASE_DURATION, team=phase.team)
        else:
            logger.info("Ending round_phase, revealing cards and switching teams")
            self.event_sender.send_reveal_cards()
            self.event_sender.broadcast_cards(self.selected_cards)
            self.set_phase(phase_name=PHASE_HINT, duration=HINT_PHASE_DURATION, team=next_team)

        self.start_phase_cycle()

    def schedule_phase_transition(self, phase_name: str) -> None:
        phase = self.get_phase()
        if not phase or phase.name != phase_name:
            logger.warning(f"Cannot schedule transition: No matching phase '{phase_name}' found")
            return

        logger.debug(f"Scheduling transition for phase '{phase.name}'")
        phase = Phase(
            name=phase.name,
            duration=phase.duration,
            team=phase.team,
            start_time=phase.start_time
        )
        phase.schedule_transition(self._on_phase_expire)

    def handle_existing_phase(self) -> Optional[str]:
        phase = self.get_phase()
        if not phase:
            logger.warning("handle_existing_phase called, but no phase found.")
            return "no_phase"
        
        now = time.time()
        end_time = phase.start_time + phase.duration
        logger.info(f"Handling existing phase '{phase.name}' (team {phase.team}). Time left: {end_time - now:.2f}s")

        if now >= end_time:
            logger.info("Phase already expired, transitioning immediately")
            next_phase = PHASE_HINT if phase.name == PHASE_ROUND else PHASE_ROUND
            next_duration = HINT_PHASE_DURATION if next_phase == PHASE_HINT else ROUND_PHASE_DURATION
            next_team = TEAM_RED if phase.team == TEAM_BLUE else TEAM_BLUE if next_phase == PHASE_ROUND else phase.team
            self.set_phase(phase_name=next_phase, duration=next_duration, team=next_team)
            self.start_phase_cycle()
        else:
            self.schedule_phase_transition(phase.name)

    def start_phase_cycle(self) -> None:
        phase = self.get_phase()
        if not phase:
            logger.warning("start_phase_cycle called but no current phase found.")
            return

        logger.info(f"Starting new phase cycle: {phase.name} | Duration: {phase.duration} | Team: {phase.team}")
        self.event_sender.send_phase(
            phase_type=phase.name,
            duration=phase.duration,
            team=phase.team,
            start_time=phase.start_time
        )
        self.schedule_phase_transition(phase.name)

    def advance_phase(self) -> None:
        if not self.current_phase:
            logger.warning("advance_phase called but current_phase is None")
            return

        logger.info(f"Advancing from current phase: {self.current_phase.name}")
        self._on_phase_expire(self.current_phase)
