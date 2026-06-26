import pygame
from enum import Enum

# from pygame.locals import QUIT
import time

from game_field import Game_Board

DEFAULT_DISPLAY_WIDTH = 1500
DEFAULT_DISPLAY_HEIGHT = 1000

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class GameState(Enum):
    QUIT = -1
    TITLE = 0
    NEWGAME = 1
    GAMEOVER = 2


class GameData:
    mouse_pos = (0, 0)
    mouse_button = None
    game_state: GameState = None

    display: pygame.Surface = None
    display_buffer: pygame.Surface = None
    display_scaling_factor: float = 1
    display_rescaled = False

    _time_game_start: float = None
    _timer_run = False
    game_duration: float = 0

    game_board: Game_Board = None

    def init(self):
        self.display = pygame.display.set_mode(
            (DEFAULT_DISPLAY_WIDTH, DEFAULT_DISPLAY_HEIGHT),
            pygame.RESIZABLE
        )
        self.display_buffer = pygame.Surface(
            (DEFAULT_DISPLAY_WIDTH, DEFAULT_DISPLAY_HEIGHT))
        self.game_state = GameState.NEWGAME

        self.create_new_board()

    def create_new_board(self):
        self.game_board = Game_Board(game_data=self)

    def start_new_game(self):
        self.game_duration = 0
        self.create_new_board()
        self.game_state = GameState.NEWGAME

        # save score

    def timer_start(self):
        if self._timer_run == False:
            self._timer_run = True
            self._time_game_start = time.time()

    def timer_stop(self):
        self._timer_run = False

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

        self.display_rescaled = False
        self.display_buffer = pygame.Surface(
            (DEFAULT_DISPLAY_WIDTH, DEFAULT_DISPLAY_HEIGHT)
        )

        self.display.fill(BLACK)
        self.display_buffer.fill(BLUE)

        for event in pygame.event.get():
            # print(event)

            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_button = event.button

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
                # pygame.quit()
                self.game_state = GameState.QUIT
