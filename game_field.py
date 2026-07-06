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


DEFAULT_TILE_SIZE = int(800 / 10)  # tile size in px

FONT_SIZE = 36
COLOR_BG = (106, 159, 181)
COLOR_TEXT = (0, 0, 255)
COLOR_TEXT_HIGHLIGHT = (255, 0, 0)

# TODO change so its scaled
HOVER_OVERLAY = pygame.Surface(
    (DEFAULT_TILE_SIZE, DEFAULT_TILE_SIZE), pygame.SRCALPHA)
HOVER_OVERLAY.fill((0, 0, 0, 20))  # alpha 0..255; adjust for darkness


class Game_Board:
    def __init__(self, game_data: GameData = None):

        self.GRID_SIZE = 10  # board size in num tiles
        self.NUM_BOMBS = int(self.GRID_SIZE * self.GRID_SIZE * 0.1)

        self.game_data = game_data

        self.board = self._generate_board()
        self._place_bombs()
        self.tiles = self._generate_board_tiles()
        # self._tile_group = pygame.sprite.Group(self.tiles)
        self.board_surface: pygame.Surface = pygame.Surface(
            (
                DEFAULT_TILE_SIZE * self.GRID_SIZE,
                DEFAULT_TILE_SIZE * self.GRID_SIZE
            )
        )

        self.num_flags = 0
        self.game_over = False
        self.game_won = False

    def _check_win_condition(self):
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self.board[y][x] != 'm' and self.tiles[y * self.GRID_SIZE + x].state != TileState.REVEALED:
                    return False
        return True

    def _get_tile_at_pixel(self, x, y) -> GameTile:
        return self.tiles[y * self.GRID_SIZE + x]

    def _generate_board(self):
        _board = list(list(0 for _ in range(self.GRID_SIZE))
                      for _ in range(self.GRID_SIZE))
        return _board

    def _place_bombs(self):
        # Place bombs
        for _ in range(self.NUM_BOMBS):
            while True:
                x = random.randint(0, self.GRID_SIZE - 1)
                y = random.randint(0, self.GRID_SIZE - 1)
                if self.board[y][x] != 'm':
                    self.board[y][x] = 'm'
                    break

        # Calculate numbers
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self.board[y][x] == 'm':
                    continue
                count = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if 0 <= y + dy < self.GRID_SIZE and 0 <= x + dx < self.GRID_SIZE:
                            if self.board[y + dy][x + dx] == 'm':
                                count += 1
                self.board[y][x] = count
        
        # update tiles content


    def _generate_board_tiles(self):
        tiles: list[GameTile] = []

        board_width = DEFAULT_TILE_SIZE * self.GRID_SIZE
        board_start_x = (
            self.game_data.display_buffer.get_width() - board_width) / 2
        board_start_y = (
            self.game_data.display_buffer.get_height() - board_width) / 2

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
                # reveal all mines
                for tile in self.tiles:
                    if tile.content == "m":
                        tile.reveal()
                        self._update_shadows(tile)

            if tile.state == TileState.FLAGGED:
                self.num_flags += 1

        if self.game_data.game_state == GameState.NEWGAME:
            if self.game_over or self.game_won:
                self.game_data.game_state = GameState.GAMEOVER

        # Scale tile texture to window size
        # image = pygame.transform.scale(
        #     image,
        #     (
        #         DEFAULT_TILE_SIZE * self.game_data.display_scaling_factor,
        #         DEFAULT_TILE_SIZE * self.game_data.display_scaling_factor)
        # )
        # self._tile_group.draw(self.game_data.screen)

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
