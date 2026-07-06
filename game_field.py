from __future__ import annotations

import pygame
from pygame import font, sysfont
from pygame.rect import Rect
from pygame.sprite import Sprite

from game_tile import GameTile

import random
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game_data import GameData

from game_states import GameState
from game_tile import GameTile, TileState
import colors

# from game_data import GameData

DEFAULT_BOARD_SIZE = 800  # board size in px
# DEFAULT_TILE_SIZE = int(BOARD_SIZE / 10)  # tile size in px

FONT_SIZE = 36
COLOR_BG = (106, 159, 181)
COLOR_TEXT = (0, 0, 255)
COLOR_TEXT_HIGHLIGHT = (255, 0, 0)


class Game_Board:
    def __init__(self, game_data: GameData = None, grid_size: int = 10):

        self.GRID_SIZE = grid_size  # board size in num tiles
        self.NUM_BOMBS = 2
        # self.NUM_BOMBS = int(self.GRID_SIZE * self.GRID_SIZE * 0.1)
        self.TILE_SIZE = int(DEFAULT_BOARD_SIZE /
                             self.GRID_SIZE)  # tile size in px
        self.BOARD_SIZE = self.TILE_SIZE * self.GRID_SIZE

        self.game_data = game_data

        self.tiles = self._generate_board_tiles()

        # self._tile_group = pygame.sprite.Group(self.tiles)
        self.board_surface: pygame.Surface = pygame.Surface(
            (
                self.BOARD_SIZE,
                self.BOARD_SIZE
            )
        )

        self.num_flags = 0
        self.game_over = False
        self.game_won = False

    def _check_win_condition(self):
        for tile in self.tiles:
            if tile.content != "m" and tile.state != TileState.REVEALED:
                return False
        return True

    def _get_tile_at_pixel(self, x, y) -> GameTile:
        return self.tiles[y * self.GRID_SIZE + x]

    def _place_bombs(self, first_tile: GameTile = None):
        # Place bombs
        for _ in range(self.NUM_BOMBS):
            while True:
                x = random.randint(0, self.GRID_SIZE - 1)
                y = random.randint(0, self.GRID_SIZE - 1)

                target_tile = self._get_tile_at_pixel(x=x, y=y)
                if target_tile.content != 'm' and target_tile != first_tile:
                    target_tile.content = 'm'
                    break

        # Calculate numbers
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self._get_tile_at_pixel(x=x, y=y).content == 'm':
                    continue

                count = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if 0 <= y + dy < self.GRID_SIZE and 0 <= x + dx < self.GRID_SIZE:
                            if self._get_tile_at_pixel(x=x+dx, y=y+dy).content == 'm':
                                count += 1

                self._get_tile_at_pixel(x=x, y=y).content = count

        # update tiles content

    def _generate_board_tiles(self):
        tiles: list[GameTile] = []

        board_start_x = (
            self.game_data.display_buffer.get_width() - self.BOARD_SIZE) / 2
        board_start_y = (
            self.game_data.display_buffer.get_height() - self.BOARD_SIZE) / 2

        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                # create ui tile
                tiles.append(
                    GameTile(
                        center_position=(
                            x * self.TILE_SIZE + self.TILE_SIZE / 2 + board_start_x,
                            y * self.TILE_SIZE + self.TILE_SIZE / 2 + board_start_y
                        ),
                        tile_position=(x, y),
                        tile_size=self.TILE_SIZE,
                        text=0,
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
                if not self.game_data._timer_run:
                    self.game_data.timer_start()
                    self._place_bombs(first_tile=tile)

                self._update_shadows(tile)
                if tile.content == 0:
                    self._reveal_neighbor_tiles(tile)

                if tile.game_over:
                    self.game_over = True
                    # reveal all mines
                    for tile in self.tiles:
                        if tile.content == "m":
                            tile.reveal()
                            self._update_shadows(tile)

            if tile.state == TileState.FLAGGED:
                self.num_flags += 1

        if self.game_data.game_state == GameState.NEWGAME:
            if self.game_over or self.game_won:
                self.game_data.timer_stop()
                self.game_data.game_state = GameState.GAMEOVER

    def _update_shadows(self, tile: GameTile):
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

            if 0 <= nx < self.GRID_SIZE and 0 <= ny < self.GRID_SIZE:
                temp_tile = self._get_tile_at_pixel(nx, ny)
                temp_tile.add_shadow_direction(i + 1)

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
                        0 <= x + xd < self.GRID_SIZE) and (
                        0 <= y + yd < self.GRID_SIZE):
                    neighbors.append(
                        self._get_tile_at_pixel(x=x + xd, y=y + yd))
        return neighbors
