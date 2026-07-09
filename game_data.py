
from __future__ import annotations

import pygame

# from pygame.locals import QUIT
import time
import json

from pathlib import Path
from game_states import GameState, DifficultyLevel
from game_field import Game_Board

DEFAULT_DISPLAY_WIDTH = 1500
DEFAULT_DISPLAY_HEIGHT = 1000

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

PATH_SCORE_FILE = Path("scores.json")

# Brettgröße und Bombenanzahl pro Schwierigkeitsstufe
DIFFICULTY_SETTINGS = {
    DifficultyLevel.EASY: {"grid_size": 8, "num_bombs": 6},
    DifficultyLevel.MEDIUM: {"grid_size": 12, "num_bombs": 18},
    DifficultyLevel.HARD: {"grid_size": 16, "num_bombs": 30},
}

# Vorgespeicherte Entwickler-Bestzeiten
# Diese sind immer in der Rangliste sichtbar und dienen als Ziel zum Übertreffen.
DEFAULT_SCORES = {
    DifficultyLevel.EASY.name: {
        "Joana": 29.66,
        "Josi": 13.41,
        "Philipp": 5.61,
    },
    DifficultyLevel.MEDIUM.name: {
        "Joana": 175.3,
        "Josi": 69.84,
        "Philipp": 40.38,
    },
    DifficultyLevel.HARD.name: {
        "Joana": 150,
        "Josi": 65.78,
        "Philipp": 60.11,
    },
}


class GameData:
    mouse_pos = (0, 0)
    mouse_button = None
    # KEYDOWN-Events des aktuellen Frames (für Texteingabe)
    key_events: list = []
    game_state: GameState = None

    display: pygame.Surface = None
    display_buffer: pygame.Surface = None
    display_scaling_factor: float = 1
    display_rescaled = False

    _time_game_start: float = None
    _timer_run = False
    game_duration: float = 0

    game_board: Game_Board = None

    player_name: str = None
    difficulty: DifficultyLevel
    _score_data: dict[str, dict[str, float]] = None

    def init(self):

        # Fenstertitel
        pygame.display.set_caption("Sandstorm")

        # Custom Icon (nutzt einfach dein Minen-Asset)
        icon = pygame.image.load("assets/icon_32.png")
        pygame.display.set_icon(icon)

        self.display = pygame.display.set_mode(
            (DEFAULT_DISPLAY_WIDTH, DEFAULT_DISPLAY_HEIGHT),
            pygame.RESIZABLE
        )

        self.display_buffer = pygame.Surface(
            (DEFAULT_DISPLAY_WIDTH, DEFAULT_DISPLAY_HEIGHT))
        self.game_state = GameState.NEWGAME

        self.player_name = "Spieler"
        self.difficulty = DifficultyLevel.EASY

        self.load_score()

        self.create_new_board()

    ####################################################################################################
    # Game
    ####################################################################################################
    def create_new_board(self):
        settings = DIFFICULTY_SETTINGS[self.difficulty]
        self.game_board = Game_Board(
            game_data=self,
            grid_size=settings["grid_size"],
            num_bombs=settings["num_bombs"]
        )

    def start_new_game(self):
        self.game_duration = 0
        self._timer_run = False  # wichtig: sonst werden im neuen Spiel keine Bomben platziert
        self.create_new_board()
        self.game_state = GameState.NEWGAME

    ####################################################################################################
    # Timer
    ####################################################################################################
    def timer_start(self):
        if self._timer_run == False:
            self._timer_run = True
            self._time_game_start = time.time()

    def timer_stop(self):
        self._timer_run = False

        if self.game_board.game_won:
            self.save_score()
            # save score
    ####################################################################################################
    # Score
    ####################################################################################################

    def save_score(self):
        self.load_score()

        # prepare score file if new
        if self._score_data is None:
            self._score_data = {}
            for dl in DifficultyLevel:
                self._score_data[dl.name] = {}
                # self.difficulty.name: self.game_duration

        # nur speichern, wenn es die erste oder eine bessere Zeit ist
        old_time = self._score_data[self.difficulty.name].get(self.player_name)
        if old_time is not None and self.game_duration >= old_time:
            return

        self._score_data[self.difficulty.name][self.player_name] = self.game_duration

        with open(PATH_SCORE_FILE, "w") as f:
            json.dump(
                self._score_data,
                f,
                indent=4
            )

    def get_scoreboard(self) -> tuple[list, tuple | None]:
        """Rangliste für die aktuell gewählte Schwierigkeitsstufe.

        Returns
        -------
        top5 : list[tuple[int, str, float]]
            Liste von (Rang, Name, Zeit), aufsteigend nach Zeit sortiert.
        player_entry : tuple[int, str, float] | None
            Extra-Eintrag für den aktuellen Spieler, falls er eine Zeit
            hat, aber nicht in den Top 5 ist. Sonst None.
        """
        scores: dict[str, float] = dict(
            DEFAULT_SCORES.get(self.difficulty.name, {})
        )
        if self._score_data is not None:
            scores.update(self._score_data.get(self.difficulty.name, {}))

        ranked = sorted(scores.items(), key=lambda kv: kv[1])

        top5 = [
            (i + 1, name, duration)
            for i, (name, duration) in enumerate(ranked[:5])
        ]

        player_entry = None
        for i, (name, duration) in enumerate(ranked):
            if name == self.player_name and i >= 5:
                player_entry = (i + 1, name, duration)
                break

        return top5, player_entry

    def load_score(self):
        if PATH_SCORE_FILE.exists():
            with open(PATH_SCORE_FILE, "r") as f:
                raw_data = json.load(f)
                print(raw_data)
                self._score_data = raw_data

    ####################################################################################################
    #
    ####################################################################################################
    def update(self):

        # Update Timer if active
        if self._timer_run:
            self.game_duration = time.time() - self._time_game_start

        # Mouse data
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_pos = (
            self.mouse_pos[0] / self.display_scaling_factor,
            self.mouse_pos[1] / self.display_scaling_factor
        )
        self.mouse_button = None  # Reset mouse button state each frame
        self.key_events = []  # Reset keyboard events each frame

        self.display_rescaled = False
        self.display_buffer = pygame.Surface(
            (DEFAULT_DISPLAY_WIDTH, DEFAULT_DISPLAY_HEIGHT)
        )

        self.display.fill(BLACK)
        self.display_buffer.fill(BLUE)

        # print(game_data.game_board.game_won, game_data.game_board.game_over)

        # print(game_data.game_board.game_won, game_data.game_board.game_over)

        for event in pygame.event.get():
            # print(event)

            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_button = event.button

            if event.type == pygame.KEYUP:
                # if event.type == pygame.KEYDOWN:
                self.key_events.append(event)

            if event.type == pygame.VIDEORESIZE:

                # self.display = pygame.display.set_mode(
                #     (
                #         max(DEFAULT_DISPLAY_WIDTH, event.w),
                #         max(DEFAULT_DISPLAY_HEIGHT, event.h)
                #     ),
                #     pygame.RESIZABLE
                # )
                # if event.w < DEFAULT_DISPLAY_WIDTH or event.h < DEFAULT_DISPLAY_HEIGHT:
                #     self.display = pygame.display.set_mode(
                #         (
                #             max(DEFAULT_DISPLAY_WIDTH, event.w),
                #             max(DEFAULT_DISPLAY_HEIGHT, event.h)
                #         ),
                #         pygame.RESIZABLE,

                #     )
                # self.display.size = (
                #     max(DEFAULT_DISPLAY_WIDTH, event.w),
                #     max(DEFAULT_DISPLAY_HEIGHT, event.h)
                # )

                self.display_scaling_factor = min(
                    self.display.get_width() / DEFAULT_DISPLAY_WIDTH,
                    self.display.get_height() / DEFAULT_DISPLAY_HEIGHT
                )
                self.display_rescaled = True
                print(self.display.get_size(), self.display_scaling_factor)

            if event.type == pygame.QUIT:
                # pygame.quit() # TODO don't use this, fix that game state is only set once by game board
                self.game_state = GameState.QUIT
