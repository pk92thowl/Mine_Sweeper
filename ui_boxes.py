import pygame
import pygame.freetype
from pygame.sprite import Sprite

from game_data import GameData
from game_states import DifficultyLevel
from buttons import Button
import colors


class UI_STAT_BOX(Sprite):
    def __init__(self, rect, image_path, font_name="Courier", font_size=20,
                 outer_color=(180, 180, 180), outer_border=(120, 120, 120),
                 left_bg=(160, 160, 160), right_bg=(255, 255, 255), padding=10,
                 game_data: GameData = None,
                 align_relative_to: tuple[Sprite, int] = None
                 ):
        super().__init__()
        self.rect = pygame.Rect(rect)
        if align_relative_to is not None:
            if align_relative_to[1] == 1:
                # right
                self.rect.left = align_relative_to[0].rect.right

            elif align_relative_to[1] == 2:
                # down
                self.rect.top = align_relative_to[0].rect.bottom
            elif align_relative_to[1] == 3:
                # left
                self.rect.right = align_relative_to[0].rect.left
            elif align_relative_to[1] == 4:
                # up
                self.rect.bottom = align_relative_to[0].rect.top

        self.outer_color = outer_color
        self.outer_border = outer_border
        self.outer_border_width = 2
        self.left_bg = left_bg
        self.right_bg = right_bg
        self.padding = padding
        self.game_data: GameData = game_data

        # load image
        self._orig_image = pygame.image.load(image_path).convert_alpha()

        # font + text state
        self.font = pygame.freetype.SysFont(font_name, font_size, bold=False)
        self.text_color = (0, 0, 0)
        self._text = ""
        self._cached_surface = None
        self._dirty = True  # mark to (re)render cached surface

        # layout
        w, h = self.rect.size
        self.left_w = w // 3
        self.right_w = w - self.left_w

        # scale image once
        iw, ih = self._orig_image.get_size()
        scale = min(
            (self.left_w - self.outer_border_width * 2) / iw,
            (h - self.outer_border_width * 2) / ih
        )
        new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
        self.image_left = pygame.transform.smoothscale(
            self._orig_image, new_size)

        # Sprite image & rect for compatibility with sprite groups
        # image property will be the cached full box surface (set on first draw/update)
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.image = self.image.copy()
        self.image.fill((0, 0, 0, 0))
        self._update_cached_surface_if_needed()
        self.rect.topleft = self.rect.topleft

    def set_text(self, text):
        if text != self._text:
            self._text = text
            self._dirty = True

    def set_image(self, image_path):
        self._orig_image = pygame.image.load(image_path).convert_alpha()
        iw, ih = self._orig_image.get_size()
        w, h = self.rect.size
        left_w = w // 3
        scale = min(left_w / iw, h / ih)
        new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
        self.image_left = pygame.transform.smoothscale(
            self._orig_image, new_size)
        self._dirty = True

    def _render_text_surface(self):
        if self._text == "":
            return None
        surf, _ = self.font.render(
            self._text, fgcolor=self.text_color, bgcolor=None)
        return surf

    def _update_cached_surface_if_needed(self):
        if not self._dirty and self._cached_surface is not None:
            return
        w, h = self.rect.size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # background
        pygame.draw.rect(surf, self.outer_color, (0, 0, w, h))

        # left area
        left_w = self.left_w
        pygame.draw.rect(surf, self.left_bg, (0, 0, left_w, h))
        img_x = (left_w - self.image_left.get_width()) // 2
        img_y = (h - self.image_left.get_height()) // 2
        surf.blit(self.image_left, (img_x, img_y))

        # right inner area
        inner = pygame.Rect(left_w + self.padding, self.padding,
                            w - left_w - self.padding * 2, h - self.padding * 2)
        pygame.draw.rect(surf, self.right_bg, inner)

        # text
        text_surf = self._render_text_surface()
        if text_surf:
            tx = inner.left + 8
            ty = inner.top + (inner.height - text_surf.get_height()) // 2
            surf.blit(text_surf, (tx, ty))

        # outer border
        pygame.draw.rect(surf, self.outer_border,
                         (0, 0, w, h), self.outer_border_width)

        # cache and set as sprite image
        self._cached_surface = surf
        self.image = surf.copy()
        self._dirty = False

    def update(self, *args, **kwargs):
        # call this each frame (or only when necessary). It will refresh cached surface if dirty.
        self._update_cached_surface_if_needed()

    # Optional convenience draw when not using sprite groups:
    def draw_to(self):
        # self._update_cached_surface_if_needed()
        self.game_data.display_buffer.blit(
            self._cached_surface, self.rect.topleft)


class UI_POPUP_BOX(Sprite):
    def __init__(self, w, h, font_name="Courier", font_size=20,
                 border_color=colors.TRANSPARENT, padding=10,
                 color_text=colors.BLACK,
                 game_data: GameData = None
                 ):
        super().__init__()
        self.game_data: GameData = game_data
        self.w = w
        self.h = h

        self.color_bg = colors.TRANSPARENT
        # self.color_bg = colors.BLUE
        self.border_color = border_color
        self.outer_border_width = 2
        self.padding = padding

        # font + text state
        self.font = pygame.freetype.SysFont(font_name, font_size, bold=True)
        self.text_color = color_text
        self._text = ""
        self._cached_surface = None
        self._dirty = True  # mark to (re)render cached surface

        self._visible = False

        self.restart_button = Button(
            game_data=game_data,
            center_position=(
                self.game_data.display_buffer.get_rect().centerx,
                self.game_data.display_buffer.get_rect().centery+h/2 - 40
            ),
            text="Restart",
            font_size=font_size,
            text_rgb=colors.WHITE,
            bg_rgb=colors.TRANSPARENT
            # bg_rgb=colors.GREY
        )

    def set_text(self, text):
        if text != self._text:
            self._text = text
            self._dirty = True

    def set_text_color(self, color):
        if color != self.text_color:
            self.text_color = color
            self._dirty = True

    def _render_text_surface(self):
        if self._text == "":
            return None
        surf, _ = self.font.render(
            self._text, fgcolor=self.text_color, bgcolor=None)
        return surf

    def _update_cached_surface_if_needed(self):
        if not self._dirty and self._cached_surface is not None:
            return

        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

        # background
        pygame.draw.rect(surf, self.color_bg, (0, 0, self.w, self.h))

        # right inner area
        # inner = pygame.Rect(
        #     self.padding, self.padding,
        #     self.w - self.padding * 2,
        #     self.h - self.padding * 2
        # )
        # pygame.draw.rect(surf, self.right_bg, inner)

        # text
        text_surf = self._render_text_surface()
        if text_surf:
            tx = surf.get_rect().centerx - text_surf.get_width() / 2
            # tx = inner.left + 8
            # ty = surf.get_rect().centery - text_surf.get_height() / 2
            ty = self.padding
            # ty = inner.top + (inner.height - text_surf.get_height()) // 2
            surf.blit(text_surf, (tx, ty))

        # outer border
        pygame.draw.rect(surf, self.border_color,
                         (0, 0, self.w, self.h), self.outer_border_width)

        # cache and set as sprite image
        self._cached_surface = surf
        self._dirty = False

    @property
    def rect(self):
        return self._cached_surface.get_rect()

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    def update(self, *args, **kwargs):
        # call this each frame (or only when necessary). It will refresh cached surface if dirty.
        # self._update_cached_surface_if_needed()

        if self._visible:
            self.restart_button.update()
            if self.restart_button.pressed:
                self.game_data.start_new_game()

    # Optional convenience draw when not using sprite groups:
    def draw_to(self):
        if self._visible:
            self._update_cached_surface_if_needed()
            self.game_data.display_buffer.blit(
                self._cached_surface,
                (
                    self.game_data.display_buffer.get_rect().centerx - self.rect.width / 2,
                    self.game_data.display_buffer.get_rect().centery - self.rect.height / 2
                )
            )

            self.restart_button.draw()

            # print(
            #     self.rect,
            #     self._visible,
            #     " ",
            #     self.game_data.display_buffer.get_rect().centerx,
            #     self.rect.width / 2,
            #     self.game_data.display_buffer.get_rect().centerx - self.rect.width / 2,
            #     " ",
            #     self.game_data.display_buffer.get_rect().centery,
            #     self.rect.height / 2,
            #     self.game_data.display_buffer.get_rect().centery - self.rect.height / 2,
            #     "",
            #     self.restart_button.rect
            # )


class UI_DIFFICULTY_SELECTOR(Sprite):
    """Klickbares UI-Element im Stil der UI_STAT_BOX.

    Zeigt die aktuelle Schwierigkeitsstufe an und rotiert beim
    Anklicken (Linksklick) durch alle Stufen des DifficultyLevel-Enums.
    Bei jedem Wechsel wird ein neues Spiel gestartet.
    """

    DIFFICULTY_COLORS = {
        DifficultyLevel.EASY: (0, 140, 0),
        DifficultyLevel.MEDIUM: (200, 160, 0),
        DifficultyLevel.HARD: (200, 0, 0),
    }

    def __init__(self, rect, font_name="Courier", font_size=20,
                 outer_color=(180, 180, 180), outer_border=(120, 120, 120),
                 inner_bg=(255, 255, 255), padding=6,
                 game_data: GameData = None,
                 align_relative_to: tuple[Sprite, int] = None):
        super().__init__()
        self.rect = pygame.Rect(rect)

        # gleiche Ausrichtungslogik wie UI_STAT_BOX
        if align_relative_to is not None:
            if align_relative_to[1] == 1:    # rechts daneben
                self.rect.left = align_relative_to[0].rect.right
            elif align_relative_to[1] == 2:  # darunter
                self.rect.top = align_relative_to[0].rect.bottom
            elif align_relative_to[1] == 3:  # links daneben
                self.rect.right = align_relative_to[0].rect.left
            elif align_relative_to[1] == 4:  # darüber
                self.rect.bottom = align_relative_to[0].rect.top

        self.game_data = game_data
        self.outer_color = outer_color
        self.outer_border = outer_border
        self.outer_border_width = 2
        self.inner_bg = inner_bg
        self.padding = padding

        self.font_label = pygame.freetype.SysFont(font_name, 12, bold=False)
        self.font_value = pygame.freetype.SysFont(
            font_name, font_size, bold=True)

        self._mouse_over = False
        self._shown_difficulty = None   # zuletzt gerenderte Stufe
        self._cached_surface = None
        self._dirty = True

        self.HOVER_OVERLAY = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.HOVER_OVERLAY.fill((0, 0, 0, 25))

    def _cycle_difficulty(self):
        levels = list(DifficultyLevel)
        idx = levels.index(self.game_data.difficulty)
        self.game_data.difficulty = levels[(idx + 1) % len(levels)]
        self.game_data.start_new_game()

    def _update_cached_surface_if_needed(self):
        if not self._dirty and self._cached_surface is not None:
            return

        w, h = self.rect.size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Hintergrund + innerer Bereich
        pygame.draw.rect(surf, self.outer_color, (0, 0, w, h))
        inner = pygame.Rect(self.padding, self.padding,
                            w - self.padding * 2, h - self.padding * 2)
        pygame.draw.rect(surf, self.inner_bg, inner)

        # kleines Label oben
        label_surf, _ = self.font_label.render(
            "Difficulty", fgcolor=(90, 90, 90), bgcolor=None)
        surf.blit(label_surf, (inner.left + 6, inner.top + 3))

        # aktuelle Stufe
        difficulty = self.game_data.difficulty
        color = self.DIFFICULTY_COLORS.get(difficulty, (0, 0, 0))
        value_surf, _ = self.font_value.render(
            difficulty.name.capitalize(), fgcolor=color, bgcolor=None)
        vx = inner.centerx - value_surf.get_width() / 2
        vy = inner.top + 3 + label_surf.get_height() + 4
        surf.blit(value_surf, (vx, vy))

        # Rahmen
        pygame.draw.rect(surf, self.outer_border,
                         (0, 0, w, h), self.outer_border_width)

        self._cached_surface = surf
        self._shown_difficulty = difficulty
        self._dirty = False

    def update(self, *args, **kwargs):
        # neu rendern, falls sich die Stufe von außen geändert hat
        if self._shown_difficulty != self.game_data.difficulty:
            self._dirty = True

        if self.rect.collidepoint(self.game_data.mouse_pos):
            self._mouse_over = True
            if self.game_data.mouse_button == 1:  # Linksklick -> rotieren
                self._cycle_difficulty()
                self._dirty = True
        else:
            self._mouse_over = False

    def draw_to(self):
        self._update_cached_surface_if_needed()
        self.game_data.display_buffer.blit(
            self._cached_surface, self.rect.topleft)
        if self._mouse_over:
            self.game_data.display_buffer.blit(
                self.HOVER_OVERLAY, self.rect.topleft)


class UI_SCOREBOARD(Sprite):
    """Zeigt die Top-5-Zeiten der aktuell gewählten Schwierigkeitsstufe.

    Ist der aktuelle Spieler nicht in den Top 5, wird er darunter als
    Extra-Eintrag mit seinem echten Rang angezeigt.
    Spalten: Rang | Name | Zeit
    """

    def __init__(self, rect, font_name="Courier", font_size=18,
                 outer_color=(180, 180, 180), outer_border=(120, 120, 120),
                 inner_bg=(255, 255, 255), padding=8,
                 game_data: GameData = None,
                 align_relative_to: tuple[Sprite, int] = None):
        super().__init__()
        self.rect = pygame.Rect(rect)

        if align_relative_to is not None:
            if align_relative_to[1] == 1:    # rechts daneben
                self.rect.left = align_relative_to[0].rect.right
            elif align_relative_to[1] == 2:  # darunter
                self.rect.top = align_relative_to[0].rect.bottom
            elif align_relative_to[1] == 3:  # links daneben
                self.rect.right = align_relative_to[0].rect.left
            elif align_relative_to[1] == 4:  # darüber
                self.rect.bottom = align_relative_to[0].rect.top

        self.game_data = game_data
        self.outer_color = outer_color
        self.outer_border = outer_border
        self.outer_border_width = 2
        self.inner_bg = inner_bg
        self.padding = padding

        self.font_title = pygame.freetype.SysFont(font_name, font_size, bold=True)
        self.font_row = pygame.freetype.SysFont(font_name, font_size - 2, bold=False)
        self.font_row_highlight = pygame.freetype.SysFont(
            font_name, font_size - 2, bold=True)

        self.row_height = font_size + 6
        self.color_text = (0, 0, 0)
        self.color_header = (90, 90, 90)
        self.color_player = (0, 0, 200)

        self._snapshot = None       # zuletzt gerenderte Daten
        self._cached_surface = None
        self._dirty = True

    @staticmethod
    def _format_row(rank, name, duration, max_name_len=10):
        name = name[:max_name_len]
        return f"{rank:>2}. {name:<{max_name_len}} {duration:>7.2f}s"

    def _update_cached_surface_if_needed(self):
        if not self._dirty and self._cached_surface is not None:
            return

        top5, player_entry = self._snapshot[1], self._snapshot[2]

        w, h = self.rect.size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(surf, self.outer_color, (0, 0, w, h))
        inner = pygame.Rect(self.padding, self.padding,
                            w - self.padding * 2, h - self.padding * 2)
        pygame.draw.rect(surf, self.inner_bg, inner)

        x = inner.left + 8
        y = inner.top + 6

        # Titel
        title = f"Top 5 - {self.game_data.difficulty.name.capitalize()}"
        title_surf, _ = self.font_title.render(
            title, fgcolor=self.color_text, bgcolor=None)
        surf.blit(title_surf, (x, y))
        y += title_surf.get_height() + 8

        # Kopfzeile
        header = f"{'#':>2}  {'Name':<10} {'Zeit':>8}"
        header_surf, _ = self.font_row.render(
            header, fgcolor=self.color_header, bgcolor=None)
        surf.blit(header_surf, (x, y))
        y += self.row_height

        pygame.draw.line(surf, self.color_header,
                         (x, y - 2), (inner.right - 8, y - 2), 1)
        y += 2

        if not top5:
            empty_surf, _ = self.font_row.render(
                "Noch keine Zeiten", fgcolor=self.color_header, bgcolor=None)
            surf.blit(empty_surf, (x, y))
        else:
            for rank, name, duration in top5:
                is_player = (name == self.game_data.player_name)
                font = self.font_row_highlight if is_player else self.font_row
                color = self.color_player if is_player else self.color_text

                row_surf, _ = font.render(
                    self._format_row(rank, name, duration),
                    fgcolor=color, bgcolor=None)
                surf.blit(row_surf, (x, y))
                y += self.row_height

            # Extra-Eintrag: Spieler außerhalb der Top 5
            if player_entry is not None:
                sep_surf, _ = self.font_row.render(
                    "...", fgcolor=self.color_header, bgcolor=None)
                surf.blit(sep_surf, (x, y))
                y += self.row_height

                rank, name, duration = player_entry
                row_surf, _ = self.font_row_highlight.render(
                    self._format_row(rank, name, duration),
                    fgcolor=self.color_player, bgcolor=None)
                surf.blit(row_surf, (x, y))

        pygame.draw.rect(surf, self.outer_border,
                         (0, 0, w, h), self.outer_border_width)

        self._cached_surface = surf
        self._dirty = False

    def update(self, *args, **kwargs):
        top5, player_entry = self.game_data.get_scoreboard()
        snapshot = (self.game_data.difficulty, tuple(top5), player_entry)

        if snapshot != self._snapshot:
            self._snapshot = snapshot
            self._dirty = True

    def draw_to(self):
        self._update_cached_surface_if_needed()
        self.game_data.display_buffer.blit(
            self._cached_surface, self.rect.topleft)
