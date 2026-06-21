import pygame
from enum import Enum

from pygame.locals import QUIT
import time


class GameState(Enum):
    QUIT = -1
    TITLE = 0
    NEWGAME = 1
    GAMEOVER = 2


class GameData:
    def __init__(self):
        self.mouse_pos = (0, 0)
        self.mouse_button = None

        self.screen: pygame.Surface = None
        self.game_state: GameState = None

    def update(self):
        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_button = None  # Reset mouse button state each frame

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_button = event.button
                
            if event.type == QUIT:
                # pygame.quit()
                self.game_state = GameState.QUIT
