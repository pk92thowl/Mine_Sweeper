
from enum import Enum

class GameState(Enum):
    QUIT = -1
    TITLE = 0
    NEWGAME = 1
    GAMEOVER = 2

class DifficultyLevel(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2
