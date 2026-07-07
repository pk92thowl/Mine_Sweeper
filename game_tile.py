from __future__ import annotations

import pygame
from pygame import font, sysfont
from pygame.rect import Rect
from pygame.sprite import Sprite

from enum import Enum
from pathlib import Path

import random
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game_data import GameData

import colors
import sounds

from game_states import GameState
# from game_data import GameData, GameState


# self.tile_size = int(800 / 10)  # tile size in px

FONT_SIZE = 36
COLOR_BG = (106, 159, 181)
COLOR_TEXT = (0, 0, 255)
COLOR_TEXT_HIGHLIGHT = (255, 0, 0)


class TileState(Enum):
    HIDDEN = 0
    FLAGGED = 1
    REVEALED = 2


class GameTile(Sprite):
    """ A user interface element that can be added to a surface """
    center_position: tuple[int, int]
    """pygame coordinates"""

    tile_position: tuple[int, int]
    """position on the game board"""

    _shadow_mask_direction: list[int]
    """ 1 = right
        2 = down
        3 = left
        4 = up
    """
    _shadow_mask = None

    def __init__(self, center_position: tuple[int, int], tile_position: tuple[int, int], tile_size, text, game_data: GameData = None):
        self.center_position = center_position
        self.tile_position = tile_position
        self.tile_size = tile_size

        self.game_data = game_data

        self._mouse_over = False
        self.state = TileState.HIDDEN
        self.game_over = False

        self._shadow_mask_direction = []
        self._update_shadow_mask()

        # Options: " " for safe tile, "f" for flagged tile, "m" for mine tile, digit for number of adjacent mines
        self._content = text
        self._base_image = None
        """Tile base texture (randomized on create)"""
        self._image_cache = None
        self._image_cache_dirty = True

        self.HOVER_OVERLAY = pygame.Surface(
            (self.tile_size, self.tile_size), pygame.SRCALPHA)
        # alpha 0..255; adjust for darkness
        self.HOVER_OVERLAY.fill((0, 0, 0, 20))

        super().__init__()

        # print(self.rect)

    def add_shadow_direction(self, direction: int):
        if 1 <= direction <= 4:
            self._shadow_mask_direction.append(direction)
            self._image_cache_dirty = True

    def _update_shadow_mask(self):
        """

        Parameters
        ----------
        size : _type_
            _description_
        dark_alpha : int, optional
            _description_, by default 180
        highlight_alpha : int, optional
            _description_, by default 80
        directions : _type_, optional
                1 = right
                2 = down
                3 = left
                4 = up


        Returns
        -------
        _type_
            _description_
        """

        size = (self.tile_size, self.tile_size)
        dark_alpha = 140
        highlight_alpha = 10

        w, h = size
        mask = pygame.Surface((w, h), pygame.SRCALPHA)

        cx, cy = w // 2, h // 2
        max_r = min(cx, cy)

        for y in range(h):
            for x in range(w):
                dx, dy = x - cx, y - cy
                r = math.hypot(dx, dy) / max_r  # 0..1
                # darkening stronger near center (use r^2 for steeper falloff)
                a = int(dark_alpha * (1 - r * r))
                if a > 0:
                    mask.set_at((x, y), (0, 0, 0, a))

        for y in range(h):
            for x in range(w):
                d = max_r
                if 1 in self._shadow_mask_direction:
                    if x >= cx:
                        d = min(d, abs(cy - y))

                if 3 in self._shadow_mask_direction:
                    if x <= cx:
                        d = min(d, abs(cy - y))

                if 2 in self._shadow_mask_direction:
                    if y >= cy:
                        d = min(d, abs(cx - x))

                if 4 in self._shadow_mask_direction:
                    if y <= cy:
                        d = min(d, abs(cx - x))

                d = d / max_r
                a = int(dark_alpha * (1 - d * d))

                if a > 0:
                    old = mask.get_at((x, y))
                    new_a = max(min(255, a), old.a)
                    mask.set_at(
                        (x, y), (old.r, old.g, old.b, new_a)
                    )
                    # mask.set_at((x, y), (0, 0, 0, a))

        # optional rim highlight: small blurred white ring near top-left of dip
        # for y in range(h):
        #     for x in range(w):
        #         dx, dy = x-(cx-6), y-(cy-6)  # offset highlight to simulate light
        #         r = math.hypot(dx, dy) / max_r
        #         if 0.6 < r < 0.95:
        #             ha = int(highlight_alpha * (1 - (r-0.6)/0.35))
        #             if ha > 0:
        #                 old = mask.get_at((x, y))
        #                 # lighter by reducing black alpha slightly (blend)
        #                 new_a = max(min(255, old.a - ha),0)

        #                 print(old.a, ha, old.a - ha, new_a)

        #                 mask.set_at(
        #                     (x, y), (old.r, old.g, old.b, new_a)
        #                     )

        #     print("end")

        self._shadow_mask = mask

    def _generate_image(self):
        """ Returns surface with text written on """
        # font = pygame.freetype.SysFont("Courier", font_size, bold=True)
        # image, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)

        image = self._get_base_image().copy()

        if self.state == TileState.HIDDEN:
            pass  # sand

        elif self.state == TileState.FLAGGED:
            flag_img = pygame.image.load(
                Path("assets/flag.png")
            ).convert_alpha()
            flag_img = pygame.transform.scale(
                flag_img,
                (self.tile_size, self.tile_size)
            )
            image.blit(flag_img, (0, 0))

        elif self.state == TileState.REVEALED:
            # Simulate a hole
            self._update_shadow_mask()
            image.blit(self._shadow_mask, (0, 0),
                       special_flags=pygame.BLEND_PREMULTIPLIED)

            if self._content == 'm':
                mine_img = pygame.image.load(
                    Path("assets/mine_2.png")).convert_alpha()
                mine_img = pygame.transform.scale(
                    mine_img,
                    (self.tile_size * 0.75, self.tile_size * 0.75)
                )

                image.blit(
                    mine_img,
                    mine_img.get_rect(
                        center=(self.tile_size / 2, self.tile_size / 2))
                )

            else:
                if isinstance(self._content, int) and self._content > 0:
                    font = pygame.freetype.SysFont(
                        "Courier",
                        FONT_SIZE,
                        bold=True
                    )

                    color = colors.BLUE
                    if self._content == 2:
                        color = colors.YELLOW
                    elif self._content >= 3:
                        # color = colors.RED
                        # map (3, 8, 255, 0)
                        color = (
                            ((255) / (8 - 3)) * (8 - self._content),
                            0,
                            0
                        )

                    text_img, _ = font.render(
                        text=str(self._content),
                        fgcolor=color,  # TODO color based on number
                        bgcolor=None
                    )

                    text_img = pygame.transform.scale(
                        text_img,
                        (self.tile_size * 0.5, self.tile_size * 0.5)
                    )

                    text_rect = text_img.get_rect(
                        center=(self.tile_size / 2, self.tile_size / 2))

                    image.blit(text_img, text_rect)

        # show tile data for debugging
        # font = pygame.freetype.SysFont("Courier", 18, bold=True)
        # text_img, _ = font.render(
        #     text=str(self.content), fgcolor=COLOR_TEXT_HIGHLIGHT, bgcolor=None)
        # text_img: pygame.surface.Surface
        # text_rect = text_img.get_rect(bottomright=(TILE_SIZE, TILE_SIZE))

        # image.blit(text_img, text_rect)
        self._image_cache = image

    def _get_base_image(self):
        if self._base_image is None:
            image_path: Path = Path("assets/sand_2.png")
            self._base_image = pygame.image.load(image_path).convert_alpha()
            self._base_image = pygame.transform.scale(
                self._base_image,
                (self.tile_size, self.tile_size)
            )

            if random.randint(0, 1) == 0:
                self._base_image = pygame.transform.rotate(
                    self._base_image, 90)

        return self._base_image

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, content):
        self._content = content
        self._image_cache_dirty = True

    @property
    def image(self):
        # or self.game_data.display_rescaled:
        if self._image_cache_dirty or self._image_cache is None:
            self._generate_image()
            self._image_cache_dirty = False

        return self._image_cache

    @property
    def rect(self):
        # return pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        # return pygame.Rect(width=TILE_SIZE, height=TILE_SIZE, center_position = self.center_position).get_rect()
        #  self.image.get_rect(center=self.center_position)
        return self.image.get_rect(center=self.center_position)

    def reveal(self, play_sound=False):

        if self.state == TileState.HIDDEN:
            self.state = TileState.REVEALED

            self._image_cache_dirty = True

            if self._content == 'm':
                # Game over
                self.game_over = True

                if play_sound:
                    sounds.play_explosion()
            else:
                if play_sound:
                    sounds.play_reveal()

            return self.state
        return None

    def flag(self, play_sound=False):
        if self.state == TileState.HIDDEN:
            self.state = TileState.FLAGGED

            if play_sound:
                sounds.play_flag_place()

        elif self.state == TileState.FLAGGED:
            self.state = TileState.HIDDEN

            if play_sound:
                sounds.play_flag_remove()

        self._image_cache_dirty = True
        return self.state

    def update(self):
        """ Updates the mouse_over variable and returns the button's
            action value when clicked.
        """

        if self.rect.collidepoint(self.game_data.mouse_pos) and self.game_data.game_state == GameState.NEWGAME:
            self._mouse_over = True
            if self.game_data.mouse_button == 1:  # Left mouse button
                return self.reveal(True)

            elif self.game_data.mouse_button == 3:  # Right mouse button
                return self.flag(True)
        else:
            self._mouse_over = False

        return None

    def draw(self, target_surface: pygame.Surface = None):
        """ Draws element onto a surface """
        if target_surface is None:
            target_surface = self.game_data.display_buffer
        target_surface.blit(self.image, self.rect)

        if self._mouse_over:
            target_surface.blit(self.HOVER_OVERLAY, self.rect)
