# Phase names
PHASE_HINT = "hint_phase"
PHASE_ROUND = "round_phase"

# Team names/colors
TEAM_RED = "Red"
TEAM_BLUE = "Blue"
TEAM_DRAW = "Draw"
TEAM_NEUTRAL = "Neutral"
TEAM_ASSASSIN = "Black"

# Phase durations (seconds)
HINT_PHASE_DURATION = 10
ROUND_PHASE_DURATION = 20
PHASE_CACHE_TIMEOUT_BUFFER = 5

# Event/action names (for WebSocket communication)
ACTION_CARD_CHOICE = "card_choice"
ACTION_HINT_SUBMIT = "hint_submit"
ACTION_PICKED_WORDS = "picked_words"
EVENT_CHOOSE_CARD = "choose_card"
EVENT_HINT_DISPLAY = "hint_display"
EVENT_SYNC_TIME = "sync_time"
EVENT_PHASE = "phase_event"
EVENT_REVEAL_CARDS = "reveal_cards"
EVENT_PLAYER_JOIN = "player_join"
EVENT_GAME_OVER = "game_over"
EVENT_SELECTED_CARDS = "selected_cards"
EVENT_REVEAL_GUESSED_CARDS = "reveal_guessed_cards"
