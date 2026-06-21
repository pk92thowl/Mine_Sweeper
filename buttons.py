import pygame
import pygame.freetype
from pygame.sprite import Sprite
from pygame.rect import Rect
from enum import Enum

from game_data import GameData

FONT_SIZE = 24
COLOR_BG = (106, 159, 181)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_HIGHLIGHT = (255, 0, 0)


class ButtonActions(Enum):
    QUIT = -1
    TITLE = 0
    NEWGAME = 1


def create_surface_with_text(text, font_size, text_rgb, bg_rgb):
    """ Returns surface with text written on """
    font = pygame.freetype.SysFont("Courier", font_size, bold=True)
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)
    return surface.convert_alpha()


class Button(Sprite):
    """ An user interface element that can be added to a surface """

    def __init__(self, center_position, text, font_size, bg_rgb, text_rgb, game_data: GameData, action=None,):
        """
        Args:
            center_position - tuple (x, y)
            text - string of text to write
            font_size - int
            bg_rgb (background colour) - tuple (r, g, b)
            text_rgb (text colour) - tuple (r, g, b)
            action - the gamestate change associated with this button
        """
        self.game_data = game_data
        self._mouse_over = False

        default_image = create_surface_with_text(
            text=text, font_size=font_size, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        highlighted_image = create_surface_with_text(
            text=text, font_size=font_size * 1.2, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        self.images = [default_image, highlighted_image]

        self.rects = [
            default_image.get_rect(center=center_position),
            highlighted_image.get_rect(center=center_position),
        ]

        self.action = action

        super().__init__()

    @property
    def image(self):
        return self.images[1] if self._mouse_over else self.images[0]

    @property
    def rect(self):
        return self.rects[1] if self._mouse_over else self.rects[0]

    def update(self, mouse_pos, mouse_button):
        """ Updates the mouse_over variable and returns the button's
            action value when clicked.
        """
        if self.rect.collidepoint(mouse_pos):
            self._mouse_over = True
            if mouse_button == 1:  # Left mouse button
                return self.action
        else:
            self._mouse_over = False
            
    def update2(self):
        """ Updates the mouse_over variable and returns the button's
            action value when clicked.
        """
        if self.rect.collidepoint(self.game_data.mouse_pos):
            self._mouse_over = True
            if self.game_data.mouse_button == 1:  # Left mouse button
                return self.action
        else:
            self._mouse_over = False

    def draw(self):
        """ Draws element onto a surface """
        self.game_data.display_buffer.blit(self.image, self.rect)
