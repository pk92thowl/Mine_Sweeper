import pygame
from pygame import font, sysfont
from pygame.rect import Rect
from pygame.sprite import Sprite

from enum import Enum
from pathlib import Path

import random
import math

from game_data import GameData


NUM_BOMBS = 10
GRID_SIZE = 10 # board size in num tiles
DEFAULT_TILE_SIZE = 64 # tile size in px

FONT_SIZE = 36
COLOR_BG = (106, 159, 181)
COLOR_TEXT = (0, 0, 255)
COLOR_TEXT_HIGHLIGHT = (255, 0, 0)

# TODO change so its scaled
HOVER_OVERLAY = pygame.Surface((DEFAULT_TILE_SIZE, DEFAULT_TILE_SIZE), pygame.SRCALPHA)
HOVER_OVERLAY.fill((0, 0, 0, 20))  # alpha 0..255; adjust for darkness


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

    def __init__(self, center_position: tuple[int, int], tile_position: tuple[int, int], text, game_data: GameData = None, action=None):
        self.center_position = center_position
        self.tile_position = tile_position
        self.game_data = game_data

        self._mouse_over = False
        self.state = TileState.HIDDEN
        self.game_over = False

        self._shadow_mask_direction = []
        self._update_shadow_mask()

        # Options: " " for safe tile, "f" for flagged tile, "m" for mine tile, digit for number of adjacent mines
        self.content = text
        self._base_image = None
        """Tile base texture (randomized on create)"""
        self._image_cache = None
        self._image_cache_dirty = True

        self.action = action

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

        size = (DEFAULT_TILE_SIZE, DEFAULT_TILE_SIZE)
        dark_alpha = 140
        highlight_alpha = 10

        w, h = size
        mask = pygame.Surface((w, h), pygame.SRCALPHA)

        cx, cy = w//2, h//2
        max_r = min(cx, cy)

        for y in range(h):
            for x in range(w):
                dx, dy = x-cx, y-cy
                r = math.hypot(dx, dy) / max_r  # 0..1
                # darkening stronger near center (use r^2 for steeper falloff)
                a = int(dark_alpha * (1 - r*r))
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
                a = int(dark_alpha * (1-d*d))

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
                Path("assets/flag.png")).convert_alpha()
            image.blit(flag_img, (0, 0))

        elif self.state == TileState.REVEALED:
            # Simulate a hole
            self._update_shadow_mask()
            image.blit(self._shadow_mask, (0, 0),
                       special_flags=pygame.BLEND_PREMULTIPLIED)

            if self.content == 'm':
                mine_img = pygame.image.load(
                    Path("assets/mine_2.png")).convert_alpha()
                mine_img = pygame.transform.scale(mine_img, (40, 40))
                image.blit(
                    mine_img,
                    mine_img.get_rect(center=(DEFAULT_TILE_SIZE / 2, DEFAULT_TILE_SIZE / 2))
                )

            else:
                if isinstance(self.content, int) and self.content > 0:
                    font = pygame.freetype.SysFont(
                        "Courier", FONT_SIZE, bold=True)
                    text_img, _ = font.render(
                        text=str(self.content), fgcolor=COLOR_TEXT, bgcolor=None)
                    text_rect = text_img.get_rect(
                        center=(DEFAULT_TILE_SIZE / 2, DEFAULT_TILE_SIZE / 2))

                    image.blit(text_img, text_rect)

        # show tile data for debugging
        # font = pygame.freetype.SysFont("Courier", 18, bold=True)
        # text_img, _ = font.render(
        #     text=str(self.content), fgcolor=COLOR_TEXT_HIGHLIGHT, bgcolor=None)
        # text_img: pygame.surface.Surface
        # text_rect = text_img.get_rect(bottomright=(TILE_SIZE, TILE_SIZE))

        # image.blit(text_img, text_rect)

        # Scale tile texture to window size
        image = pygame.transform.scale(
            image,
            (
                DEFAULT_TILE_SIZE * self.game_data.display_scaling_factor,
                DEFAULT_TILE_SIZE * self.game_data.display_scaling_factor)
        )

        self._image_cache = image

    def _get_base_image(self):
        if self._base_image is None:
            image_path: Path = Path("assets/sand_2.png")
            self._base_image = pygame.image.load(image_path).convert_alpha()

            if random.randint(0, 1) == 0:
                self._base_image = pygame.transform.rotate(
                    self._base_image, 90)

        return self._base_image

    @property
    def image(self):
        if self._image_cache_dirty or self._image_cache is None or self.game_data.display_rescaled:
            self._generate_image()
            self._image_cache_dirty = False

        return self._image_cache

    @property
    def rect(self):
        # return pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        # return pygame.Rect(width=TILE_SIZE, height=TILE_SIZE, center_position = self.center_position).get_rect()
        #  self.image.get_rect(center=self.center_position)
        return self.image.get_rect(center=self.center_position)

    def reveal(self):
        if self.state == TileState.HIDDEN:
            self.state = TileState.REVEALED

            self._image_cache_dirty = True

            if self.content == 'm':
                # Game over
                self.game_over = True

            return self.state

    def flag(self):
        if self.state == TileState.HIDDEN:
            self.state = TileState.FLAGGED

        elif self.state == TileState.FLAGGED:
            self.state = TileState.HIDDEN

        self._image_cache_dirty = True
        return self.state

    def update(self):
        """ Updates the mouse_over variable and returns the button's
            action value when clicked.
        """
        if self.rect.collidepoint(self.game_data.mouse_pos):
            self._mouse_over = True
            if self.game_data.mouse_button == 1:  # Left mouse button
                return self.reveal()

            elif self.game_data.mouse_button == 3:  # Right mouse button
                return self.flag()
        else:
            self._mouse_over = False

    def draw(self):
        """ Draws element onto a surface """
        self.game_data.display.blit(self.image, self.rect)

        if self._mouse_over:
            self.game_data.display.blit(HOVER_OVERLAY, self.rect)


class Game_Board:
    def __init__(self, game_data: GameData = None):
        self.game_data = game_data

        self.board = self._generate_board()
        self.tiles = self._generate_board_tiles()
        self._tile_group = pygame.sprite.Group(self.tiles)

        self.num_bombs = NUM_BOMBS
        self.num_flags = 0
        self.game_over = False
        self.game_won = False

    def _check_win_condition(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.board[y][x] != 'm' and self.tiles[y*GRID_SIZE + x].state != TileState.REVEALED:
                    return False
        return True

    def _get_tile_at_pixel(self, x, y) -> GameTile:
        return self.tiles[y*GRID_SIZE+x]

    def _generate_board(self):
        _board = list(list(0 for _ in range(GRID_SIZE))
                      for _ in range(GRID_SIZE))

        # Place bombs
        for _ in range(NUM_BOMBS):
            while True:
                x = random.randint(0, GRID_SIZE - 1)
                y = random.randint(0, GRID_SIZE - 1)
                if _board[y][x] != 'm':
                    _board[y][x] = 'm'
                    break

        # Calculate numbers
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if _board[y][x] == 'm':
                    continue
                count = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if 0 <= y + dy < GRID_SIZE and 0 <= x + dx < GRID_SIZE:
                            if _board[y + dy][x + dx] == 'm':
                                count += 1
                _board[y][x] = count

        return _board

    def _generate_board_tiles(self):
        tiles: list[GameTile] = []

        board_width = DEFAULT_TILE_SIZE * GRID_SIZE
        board_start_x = (self.game_data.display.get_width() - board_width) / 2
        board_start_y = (self.game_data.display.get_height() - board_width) / 2

        for y in range(len(self.board)):
            for x in range(len(self.board[y])):
                # create ui tile
                tiles.append(
                    GameTile(
                        center_position=(
                            x * DEFAULT_TILE_SIZE + DEFAULT_TILE_SIZE / 2 + board_start_x,
                            y * DEFAULT_TILE_SIZE + DEFAULT_TILE_SIZE / 2 + board_start_y
                        ),
                        tile_position=(x, y),
                        text=self.board[y][x],
                        game_data=self.game_data
                    )
                )

        return tiles

    def update(self):
        self.num_flags = 0
        self.game_won = self._check_win_condition()
        for tile in self.tiles:
            new_state = tile.update()
            tile.draw()
            if new_state == TileState.REVEALED:
                self._update_shadows(tile)

                if tile.content == 0:
                    self._reveal_neighbor_tiles(tile)

            if tile.game_over:
                self.game_over = True

            if tile.state == TileState.FLAGGED:
                self.num_flags += 1

        # self._tile_group.draw(self.game_data.screen)

    def _update_shadows(self, tile:GameTile):
        "Updates the shadows of tile's neighbours"
        # update cardinal neighbours shadow mask
        offsets = [
            (-1, 0),  # tile to the left, needs direction 1
            (0, -1),  # tile to the top, needs direction 2
            (1, 0),  # tile to the right, needs direction 3
            (0, 1),  # tile to the bottom, needs direction 4
        ]

        for i in range(4):
            nx = tile.tile_position[0] + offsets[i][0]
            ny = tile.tile_position[1] + offsets[i][1]

            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                temp_tile = self._get_tile_at_pixel(nx, ny)
                temp_tile.add_shadow_direction(i+1)

    def _reveal_neighbor_tiles(self, tile: GameTile):
        # print(f"revealing all neighboars of tile {tile.tile_position}")
        neighbors = self._get_neighbor_tiles(
            tile.tile_position[0],
            tile.tile_position[1]
        )

        for tile in neighbors:

            if tile.state == TileState.HIDDEN:
                tile.reveal()
                self._update_shadows(tile)
                if tile.content == 0:
                    self._reveal_neighbor_tiles(tile)

    def _get_neighbor_tiles(self, x, y):
        neighbors = []
        for yd in range(-1, 2):
            for xd in range(-1, 2):
                if not (xd == 0 and yd == 0) and (
                        0 <= x+xd < GRID_SIZE) and (
                        0 <= y+yd < GRID_SIZE):
                    neighbors.append(self._get_tile_at_pixel(x=x+xd, y=y+yd))
        return neighbors
