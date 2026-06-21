import pygame
from enum import Enum

#from pygame.locals import QUIT
import time

DEFAULT_DISPLAY_WIDTH = 500
DEFAULT_DISPLAY_HEIGHT = 500


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
    display_scaling_factor: float = 1
    display_rescaled = False

    def init(self):
        self.display = pygame.display.set_mode((DEFAULT_DISPLAY_WIDTH, DEFAULT_DISPLAY_HEIGHT), pygame.RESIZABLE)
        self.game_state = GameState.NEWGAME

    def update(self):
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_button = None  # Reset mouse button state each frame
        self.display_rescaled = False

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_button = event.button

            if event.type == pygame.VIDEORESIZE:
                self.display = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self.display_scaling_factor = min(self.display.get_width() / DEFAULT_DISPLAY_WIDTH,
                                                  self.display.get_height() / DEFAULT_DISPLAY_HEIGHT)
                self.display_rescaled = True
                print(self.display.get_size(), self.display_scaling_factor)

            if event.type == pygame.QUIT:
                # pygame.quit()
                self.game_state = GameState.QUIT
