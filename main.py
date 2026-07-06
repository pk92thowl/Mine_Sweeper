import time
import pygame
import pygame.freetype
from pygame.sprite import Sprite
from pygame.rect import Rect
from pygame.locals import QUIT
from enum import Enum

import colors
from buttons import Button, ButtonActions
from ui_boxes import UI_STAT_BOX, UI_POPUP_BOX, UI_DIFFICULTY_SELECTOR
from game_data import GameData, GameState
from game_field import Game_Board

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)

game_data = GameData()


def main():
    pygame.init()

    game_data.init()

    while game_data.game_state != GameState.QUIT:
        if game_data.game_state == GameState.TITLE:
            # title_screen()
            pass

        if game_data.game_state == GameState.NEWGAME:
            play_level()

        if game_data.game_state == GameState.QUIT:
            game_data.game_state = GameState.QUIT
            pygame.quit()
            return


def play_level():
    # return_btn = Button(
    #     center_position=(game_data.display_buffer.get_width()/2,
    #                      game_data.display_buffer.get_height() - 30),
    #     font_size=20,
    #     bg_rgb=BLUE,
    #     text_rgb=WHITE,
    #     text="Return to main menu",
    #     action=GameState.TITLE,
    #     game_data=game_data
    # )

    buttons = [
        # return_btn
    ]

    ui_count_flags = UI_STAT_BOX(
        rect=Rect(
            game_data.display_buffer.get_width() / 2 - (160 / 2),
            45,
            160,
            50
        ),
        font_name="Courier",
        font_size=20,
        image_path="assets/flag.png",
        outer_color=(180, 180, 180),
        outer_border=(120, 120, 120),
        left_bg=(160, 160, 160),
        right_bg=(255, 255, 255),
        padding=10,
        game_data=game_data
    )

    ui_count_bombs = UI_STAT_BOX(
        rect=Rect(200, 45, 150, 50),
        font_name="Courier",
        font_size=20,
        image_path="assets/mine_2.png",
        outer_color=(180, 180, 180),
        outer_border=(120, 120, 120),
        left_bg=(160, 160, 160),
        right_bg=(255, 255, 255),
        padding=10,
        game_data=game_data,
        align_relative_to=(ui_count_flags, 3)
    )

    ui_timer = UI_STAT_BOX(
        rect=Rect(500, 45, 200, 50),
        font_name="Courier",
        font_size=20,
        image_path="assets/stop_watch.png",
        outer_color=(180, 180, 180),
        outer_border=(120, 120, 120),
        left_bg=(160, 160, 160),
        right_bg=(255, 255, 255),
        padding=10,
        game_data=game_data,
        align_relative_to=(ui_count_flags, 1)
    )

    # create difficulty selector
    ui_difficulty = UI_DIFFICULTY_SELECTOR(
        rect=Rect(0, 45, 160, 50),
        font_name="Courier",
        font_size=20,
        game_data=game_data,
        align_relative_to=(ui_timer, 1)  # rechts neben dem Timer
    )

    win_lose_ui_popup = UI_POPUP_BOX(
        w=400,
        h=150,
        font_size=64,
        game_data=game_data
    )

    ui_boxes: list[Sprite] = [
        ui_count_bombs,
        ui_count_flags,
        ui_timer,
        ui_difficulty,
        win_lose_ui_popup,
    ]

    # win_lose_ui_popup.show()
    # win_lose_ui_popup.set_text("test")
    # game_data.game_state = GameState.GAMEOVER

    # game_data.game_board.game_over = True

    clock = pygame.time.Clock()
    fps_min = 1000
    fps_max = 0
    while game_data.game_state != GameState.QUIT:
        game_data.update()

        # Handle Buttons
        for button in buttons:
            ui_action = button.update2()
            if ui_action is not None:
                game_data.game_state = ui_action
            button.draw()

        ui_count_bombs.set_text(f"x{game_data.game_board.NUM_BOMBS}")
        ui_count_flags.set_text(f"x{game_data.game_board.num_flags}")
        # ui_timer.set_text(f"{int(time.time()-time_start)}s")
        ui_timer.set_text(f"{game_data.game_duration:.2f}s")

        game_data.game_board.update()

        for ui_box in ui_boxes:
            ui_box.update()
            ui_box.draw_to()

        # draw game field
        # each game tile is like a button

        if game_data.game_board.game_over or game_data.game_board.game_won:
            
            win_lose_ui_popup.set_text(
                f"{'You Win' if game_data.game_board.game_won else 'You Lose'}"
            )
            win_lose_ui_popup.set_text_color(
                colors.GREEN if game_data.game_board.game_won else colors.RED
            )
            win_lose_ui_popup.show()
        else:
            win_lose_ui_popup.hide()

        # print(
        #     game_data.display_buffer,
        #     game_data.display_buffer.get_rect(),
        #     game_data.display_buffer.get_rect().width,
        #     game_data.display_buffer.get_rect().height,
        #     game_data.display_scaling_factor,
        #     game_data.display_buffer.get_rect().width * game_data.display_scaling_factor,
        #     game_data.display_buffer.get_rect().height * game_data.display_scaling_factor,
        # )

        # Scale buffer to window size
        game_data.display_buffer = pygame.transform.scale(
            game_data.display_buffer,
            (
                game_data.display_buffer.get_rect().width * game_data.display_scaling_factor,
                game_data.display_buffer.get_rect().height * game_data.display_scaling_factor
            )
        )

        # Draw buffer to window
        game_data.display.blit(game_data.display_buffer,
                               game_data.display_buffer.get_rect())

        pygame.display.flip()

        clock.tick()
        fps = clock.get_fps().__round__(2)
        if fps < fps_min and fps != 0:
            fps_min = fps
        
        if fps > fps_max:
            fps_max = fps
        print(fps, fps_min, fps_max)


if __name__ == "__main__":
    main()
