"""Tutorial-Overlay für neue Spieler.

Zeigt beim ersten Start eine Schritt-für-Schritt-Einführung als
halbtransparentes Overlay über dem Spiel. Einzelne UI-Bereiche
(Spielfeld, Statusleiste, Scoreboard, ...) werden dabei hervorgehoben.

Das Tutorial kann jederzeit übersprungen werden ("Überspringen"-Button
oder Escape). Ob das Tutorial bereits gesehen wurde, wird in
settings.json gespeichert. Über den kleinen "Hilfe"-Button kann es
jederzeit erneut gestartet werden.
"""

from __future__ import annotations

import json
from pathlib import Path

import pygame
import pygame.freetype
from pygame.rect import Rect
from pygame.sprite import Sprite

import colors

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from game_data import GameData

PATH_SETTINGS_FILE = Path("settings.json")


####################################################################################################
# Persistenz: wurde das Tutorial schon gesehen?
####################################################################################################
def _load_settings() -> dict:
    if PATH_SETTINGS_FILE.exists():
        try:
            with open(PATH_SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_settings(settings: dict):
    try:
        with open(PATH_SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except OSError:
        pass


def is_tutorial_done() -> bool:
    return _load_settings().get("tutorial_done", False)


def set_tutorial_done():
    settings = _load_settings()
    settings["tutorial_done"] = True
    _save_settings(settings)


####################################################################################################
# Tutorial-Schritte
####################################################################################################
class TutorialStep:
    def __init__(self, title: str, lines: list[str],
                 highlight: Rect | None = None):
        """
        Args:
            title     - Überschrift des Schritts
            lines     - Textzeilen mit der Erklärung
            highlight - optionaler Bereich, der hervorgehoben wird
        """
        self.title = title
        self.lines = lines
        self.highlight = highlight


####################################################################################################
# Tutorial-Overlay
####################################################################################################
class Tutorial:
    PANEL_W = 560
    BTN_W = 190
    BTN_H = 40

    def __init__(self, game_data: GameData, steps: list[TutorialStep],
                 font_name: str = "Courier"):
        self.game_data = game_data
        self.steps = steps
        self.step_index = 0
        self.active = False

        self.font_title = pygame.freetype.SysFont(font_name, 26, bold=True)
        self.font_text = pygame.freetype.SysFont(font_name, 18, bold=False)
        self.font_btn = pygame.freetype.SysFont(font_name, 18, bold=True)
        self.font_counter = pygame.freetype.SysFont(font_name, 14, bold=False)

        # werden in _layout() pro Frame gesetzt
        self._panel_rect: Rect = Rect(0, 0, 0, 0)
        self._btn_next_rect: Rect = Rect(0, 0, 0, 0)
        self._btn_skip_rect: Rect = Rect(0, 0, 0, 0)

        self._hover_next = False
        self._hover_skip = False

    # ---------------------------------------------------------------- Steuerung
    def start(self):
        self.step_index = 0
        self.active = True

    def _finish(self, skipped: bool = False):
        self.active = False
        set_tutorial_done()

    def _next(self):
        self.step_index += 1
        if self.step_index >= len(self.steps):
            self._finish()

    @property
    def _current_step(self) -> TutorialStep:
        return self.steps[self.step_index]

    @property
    def _is_last_step(self) -> bool:
        return self.step_index >= len(self.steps) - 1

    # ---------------------------------------------------------------- Layout
    def _layout(self):
        """Berechnet Panel- und Button-Positionen für den aktuellen Schritt."""
        step = self._current_step
        buffer_rect = self.game_data.display_buffer.get_rect()

        # Panelhöhe abhängig von der Textmenge
        panel_h = 90 + len(step.lines) * 26 + self.BTN_H + 30

        panel = Rect(0, 0, self.PANEL_W, panel_h)
        panel.center = buffer_rect.center

        # Falls das Panel den hervorgehobenen Bereich verdeckt:
        # unterhalb bzw. oberhalb platzieren
        if step.highlight is not None and panel.colliderect(step.highlight):
            below_top = step.highlight.bottom + 20
            above_bottom = step.highlight.top - 20

            if below_top + panel_h <= buffer_rect.height - 10:
                panel.top = below_top
            elif above_bottom - panel_h >= 10:
                panel.bottom = above_bottom
            # sonst: zentriert lassen

        self._panel_rect = panel

        self._btn_skip_rect = Rect(
            panel.left + 25,
            panel.bottom - self.BTN_H - 20,
            self.BTN_W, self.BTN_H
        )
        self._btn_next_rect = Rect(
            panel.right - self.BTN_W - 25,
            panel.bottom - self.BTN_H - 20,
            self.BTN_W, self.BTN_H
        )

    # ---------------------------------------------------------------- Update
    def update(self) -> bool:
        """Verarbeitet Eingaben. Gibt True zurück, wenn das Tutorial aktiv
        ist und die Eingaben "verbraucht" hat (damit das Spiel darunter
        nicht auf Klicks reagiert).
        """
        if not self.active:
            return False

        self._layout()

        mouse_pos = self.game_data.mouse_pos
        self._hover_next = self._btn_next_rect.collidepoint(mouse_pos)
        self._hover_skip = self._btn_skip_rect.collidepoint(mouse_pos)

        # Escape überspringt das Tutorial
        for event in self.game_data.key_events:
            if event.key == pygame.K_ESCAPE:
                self._finish(skipped=True)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                             pygame.K_SPACE):
                self._next()
                return True

        if self.game_data.mouse_button == 1:  # Linksklick
            if self._hover_next:
                self._next()
            elif self._hover_skip:
                self._finish(skipped=True)

        return True

    # ---------------------------------------------------------------- Zeichnen
    def _draw_button(self, surface: pygame.Surface, rect: Rect, text: str,
                     hover: bool, primary: bool):
        if primary:
            bg = (0, 150, 60) if not hover else (0, 180, 75)
        else:
            bg = (120, 120, 120) if not hover else (150, 150, 150)

        pygame.draw.rect(surface, bg, rect, border_radius=6)
        pygame.draw.rect(surface, colors.BLACK, rect, 2, border_radius=6)

        text_surf, _ = self.font_btn.render(
            text, fgcolor=colors.WHITE, bgcolor=None)
        surface.blit(
            text_surf,
            (
                rect.centerx - text_surf.get_width() / 2,
                rect.centery - text_surf.get_height() / 2
            )
        )

    def draw_to(self):
        if not self.active:
            return

        buffer = self.game_data.display_buffer
        step = self._current_step

        # -------- dunkles Overlay mit "Loch" für den Highlight-Bereich
        overlay = pygame.Surface(buffer.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))

        if step.highlight is not None:
            cutout = step.highlight.inflate(12, 12)
            overlay.fill((0, 0, 0, 0), cutout)

        buffer.blit(overlay, (0, 0))

        # gelber Rahmen um den hervorgehobenen Bereich
        if step.highlight is not None:
            pygame.draw.rect(
                buffer, colors.YELLOW,
                step.highlight.inflate(12, 12), 4, border_radius=4
            )

        # -------- Panel
        panel = self._panel_rect
        pygame.draw.rect(buffer, (245, 245, 235), panel, border_radius=10)
        pygame.draw.rect(buffer, colors.UI_BORDER, panel, 3, border_radius=10)

        x = panel.left + 25
        y = panel.top + 20

        # Titel
        title_surf, _ = self.font_title.render(
            step.title, fgcolor=colors.BLACK, bgcolor=None)
        buffer.blit(title_surf, (x, y))

        # Schritt-Zähler oben rechts
        counter_surf, _ = self.font_counter.render(
            f"Schritt {self.step_index + 1}/{len(self.steps)}",
            fgcolor=(110, 110, 110), bgcolor=None)
        buffer.blit(
            counter_surf,
            (panel.right - counter_surf.get_width() - 25, y + 5)
        )

        y += title_surf.get_height() + 16

        # Textzeilen
        for line in step.lines:
            if line:
                line_surf, _ = self.font_text.render(
                    line, fgcolor=(40, 40, 40), bgcolor=None)
                buffer.blit(line_surf, (x, y))
            y += 26

        # Buttons
        self._draw_button(
            buffer, self._btn_skip_rect,
            "Überspringen", self._hover_skip, primary=False
        )
        self._draw_button(
            buffer, self._btn_next_rect,
            "Los geht's!" if self._is_last_step else "Weiter →",
            self._hover_next, primary=True
        )


####################################################################################################
# Kleiner Hilfe-Button, um das Tutorial erneut zu starten
####################################################################################################
class UI_TUTORIAL_BUTTON(Sprite):
    """Klickbarer Button im Stil der anderen UI-Boxen.

    Startet das Tutorial erneut.
    """

    def __init__(self, rect, tutorial: Tutorial, font_name="Courier",
                 font_size=20,
                 outer_color=(180, 180, 180), outer_border=(120, 120, 120),
                 inner_bg=(255, 255, 255), padding=6,
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
        self.tutorial = tutorial
        self.outer_color = outer_color
        self.outer_border = outer_border
        self.outer_border_width = 2
        self.inner_bg = inner_bg
        self.padding = padding

        self.font_label = pygame.freetype.SysFont(font_name, 12, bold=False)
        self.font_value = pygame.freetype.SysFont(
            font_name, font_size, bold=True)

        self._mouse_over = False
        self._cached_surface = None
        self._dirty = True

        self.HOVER_OVERLAY = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.HOVER_OVERLAY.fill((0, 0, 0, 25))

    def _update_cached_surface_if_needed(self):
        if not self._dirty and self._cached_surface is not None:
            return

        w, h = self.rect.size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(surf, self.outer_color, (0, 0, w, h))
        inner = pygame.Rect(self.padding, self.padding,
                            w - self.padding * 2, h - self.padding * 2)
        pygame.draw.rect(surf, self.inner_bg, inner)

        label_surf, _ = self.font_label.render(
            "Hilfe", fgcolor=(90, 90, 90), bgcolor=None)
        surf.blit(label_surf, (inner.left + 6, inner.top + 3))

        value_surf, _ = self.font_value.render(
            "?", fgcolor=(0, 0, 200), bgcolor=None)
        vx = inner.centerx - value_surf.get_width() / 2
        vy = inner.top + 3 + label_surf.get_height() + 4
        surf.blit(value_surf, (vx, vy))

        pygame.draw.rect(surf, self.outer_border,
                         (0, 0, w, h), self.outer_border_width)

        self._cached_surface = surf
        self._dirty = False

    def update(self, *args, **kwargs):
        # nicht reagieren, während das Tutorial läuft
        if self.tutorial.active:
            self._mouse_over = False
            return

        if self.rect.collidepoint(self.game_data.mouse_pos):
            self._mouse_over = True
            if self.game_data.mouse_button == 1:
                self.tutorial.start()
        else:
            self._mouse_over = False

    def draw_to(self):
        self._update_cached_surface_if_needed()
        self.game_data.display_buffer.blit(
            self._cached_surface, self.rect.topleft)
        if self._mouse_over:
            self.game_data.display_buffer.blit(
                self.HOVER_OVERLAY, self.rect.topleft)
