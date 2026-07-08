import time
import pygame
import pygame.freetype
from pygame.sprite import Sprite
from pygame.rect import Rect
from pygame.locals import QUIT
from enum import Enum

import colors
import sounds
import tutorial
from tutorial import Tutorial, TutorialStep, UI_TUTORIAL_BUTTON
from buttons import Button, ButtonActions
from ui_boxes import UI_STAT_BOX, UI_POPUP_BOX, UI_DIFFICULTY_SELECTOR, UI_SCOREBOARD, UI_NAME_INPUT, UI_SOUND_TOGGLE
from game_data import GameData, GameState
from game_field import DEFAULT_BOARD_SIZE

BLUE = (106, 159, 181)
WHITE = (255, 255, 255)

game_data = GameData()


def main():
    pygame.init()
    sounds.init()

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

    # --- Statusleiste zentriert über dem Spielfeld ---
    BOX_H = 50
    GAP_TO_BOARD = 10  # kleine Lücke zwischen UI und Spielbrett

    # Breite aller UI elemente
    W_BOMBS, W_FLAGS, W_TIMER, W_DIFF, W_SOUND = 150, 160, 200, 160, 100
    W_HELP = 100  # Hilfe-Button (Tutorial)
    total_w = W_BOMBS + W_FLAGS + W_TIMER + W_DIFF + W_SOUND + W_HELP

    board_top = (game_data.display_buffer.get_height() -
                 DEFAULT_BOARD_SIZE) / 2
    bar_y = board_top - BOX_H - GAP_TO_BOARD
    bar_x = (game_data.display_buffer.get_width() - total_w) / 2

    ui_count_bombs = UI_STAT_BOX(
        rect=Rect(bar_x, bar_y, W_BOMBS, BOX_H),
        font_name="Courier",
        font_size=20,
        image_path="assets/mine_2.png",
        outer_color=(180, 180, 180),
        outer_border=(120, 120, 120),
        left_bg=(160, 160, 160),
        right_bg=(255, 255, 255),
        padding=10,
        game_data=game_data
    )

    ui_count_flags = UI_STAT_BOX(
        rect=Rect(0, bar_y, W_FLAGS, BOX_H),
        font_name="Courier",
        font_size=20,
        image_path="assets/flag.png",
        outer_color=(180, 180, 180),
        outer_border=(120, 120, 120),
        left_bg=(160, 160, 160),
        right_bg=(255, 255, 255),
        padding=10,
        game_data=game_data,
        align_relative_to=(ui_count_bombs, 1)  # rechts neben Bomben
    )

    ui_timer = UI_STAT_BOX(
        rect=Rect(0, bar_y, W_TIMER, BOX_H),
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

    ui_difficulty = UI_DIFFICULTY_SELECTOR(
        rect=Rect(0, bar_y, W_DIFF, BOX_H),
        font_name="Courier",
        font_size=20,
        game_data=game_data,
        align_relative_to=(ui_timer, 1)
    )

    ui_sound_toggle = UI_SOUND_TOGGLE(
        rect=Rect(0, bar_y, W_SOUND, BOX_H),
        font_name="Courier",
        font_size=20,
        game_data=game_data,
        align_relative_to=(ui_difficulty, 1)  # rechts neben Difficulty
    )

    # Namenseingabe links oben, direkt über dem Scoreboard
    ui_name_input = UI_NAME_INPUT(
        # rect=Rect(30, 120, 290, 60),
        rect=Rect(30, game_data.game_board.board_start_y, 290, 60),
        font_name="Courier",
        font_size=18,
        game_data=game_data
    )

    # Scoreboard links neben dem Spielfeld
    # (Board ist 800px breit und zentriert -> linker Rand hat ~350px Platz)
    ui_scoreboard = UI_SCOREBOARD(
        # rect=Rect(30, 190, 290, 260),
        rect=Rect(30, game_data.game_board.board_start_y+70, 290, 260),
        font_name="Courier",
        font_size=18,
        game_data=game_data
    )

    win_lose_ui_popup = UI_POPUP_BOX(
        w=400,
        h=150,
        font_size=64,
        game_data=game_data
    )

    # --- Tutorial für neue Spieler ---
    status_bar_rect = Rect(bar_x, bar_y, total_w, BOX_H)
    scoreboard_area_rect = ui_name_input.rect.union(ui_scoreboard.rect)

    tutorial_steps = [
        TutorialStep(
            title="Willkommen bei Minesweeper!",
            lines=[
                "Ziel des Spiels: Decke alle Felder auf,",
                "ohne dabei auf eine Mine zu klicken.",
                "",
                "Diese kurze Einführung zeigt dir die",
                "wichtigsten Funktionen. Du kannst sie",
                "jederzeit mit 'Überspringen' oder Escape beenden.",
            ],
        ),
        TutorialStep(
            title="Das Spielfeld",
            lines=[
                "Linksklick deckt ein Feld auf.",
                "",
                "Keine Sorge: Der erste Klick ist immer sicher,",
                "erst danach werden die Minen platziert.",
            ],
            highlight=game_data.game_board.border_rect,
        ),
        TutorialStep(
            title="Die Zahlen",
            lines=[
                "Eine Zahl zeigt, wie viele Minen in den",
                "8 Nachbarfeldern liegen.",
                "",
                "Beispiel: Die '2' hat genau zwei Minen",
                "als Nachbarn. Leere Felder decken ihre",
                "Nachbarn automatisch mit auf.",
            ],
            image=tutorial.create_number_example_surface(tile_size=64),
        ),
        TutorialStep(
            title="Flaggen setzen",
            lines=[
                "Rechtsklick markiert ein Feld mit einer Flagge,",
                "wenn du dort eine Mine vermutest.",
                "",
                "Ein weiterer Rechtsklick entfernt die Flagge.",
                "Der Zähler oben zeigt deine gesetzten Flaggen.",
            ],
            highlight=ui_count_flags.rect,
        ),
        TutorialStep(
            title="Die Statusleiste",
            lines=[
                "Hier siehst du die Anzahl der Minen, deine",
                "Flaggen und die laufende Zeit.",
                "",
                "Mit einem Klick auf 'Difficulty' wechselst du",
                "die Schwierigkeitsstufe, mit 'Sound' schaltest",
                "du die Töne an oder aus.",
            ],
            highlight=status_bar_rect,
        ),
        TutorialStep(
            title="Name & Bestenliste",
            lines=[
                "Klicke auf das Namensfeld, um deinen",
                "Spielernamen einzugeben.",
                "",
                "Deine besten Zeiten landen in der",
                "Top-5-Bestenliste der jeweiligen Stufe.",
            ],
            highlight=scoreboard_area_rect,
        ),
        TutorialStep(
            title="Viel Erfolg!",
            lines=[
                "Das war's schon - du bist startklar.",
                "",
                "Tipp: Über den 'Hilfe'-Button (?) oben rechts",
                "kannst du dieses Tutorial jederzeit",
                "erneut ansehen.",
            ],
        ),
    ]

    game_tutorial = Tutorial(game_data=game_data, steps=tutorial_steps)

    ui_tutorial_button = UI_TUTORIAL_BUTTON(
        rect=Rect(0, bar_y, W_HELP, BOX_H),
        font_name="Courier",
        font_size=20,
        game_data=game_data,
        tutorial=game_tutorial,
        align_relative_to=(ui_sound_toggle, 1)  # rechts neben Sound
    )

    # Tutorial nur beim ersten Start automatisch anzeigen
    if not tutorial.is_tutorial_done():
        game_tutorial.start()

    ui_boxes: list[Sprite] = [
        ui_count_bombs,
        ui_count_flags,
        ui_timer,
        ui_difficulty,
        ui_name_input,
        ui_scoreboard,
        win_lose_ui_popup,
        ui_sound_toggle,
        ui_tutorial_button
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

        # Tutorial verarbeitet Eingaben zuerst. Ist es aktiv, werden
        # Maus- und Tastatureingaben "verbraucht", damit das Spiel
        # darunter nicht darauf reagiert.
        if game_tutorial.update():
            game_data.mouse_pos = (0, 0)
            game_data.mouse_button = None
            game_data.key_events = []

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

        # Tutorial-Overlay zuletzt zeichnen (liegt über allem)
        game_tutorial.draw_to()

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
        # print(fps, fps_min, fps_max)


if __name__ == "__main__":
    main()
