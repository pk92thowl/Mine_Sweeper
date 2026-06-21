import pygame
import pygame.freetype
from pygame.sprite import Sprite

from game_data import GameData


class UI_BOX(Sprite):
    def __init__(self, rect, image_path, font_name="Courier", font_size=20,
                 outer_color=(180, 180, 180), outer_border=(120, 120, 120),
                 left_bg=(160, 160, 160), right_bg=(255, 255, 255), padding=10, game_data: GameData = None):
        super().__init__()
        self.rect = pygame.Rect(rect)
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
            (self.left_w-self.outer_border_width*2) / iw,
            (h-self.outer_border_width*2) / ih
        )
        new_size = (max(1, int(iw*scale)), max(1, int(ih*scale)))
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
        new_size = (max(1, int(iw*scale)), max(1, int(ih*scale)))
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
                            w - left_w - self.padding*2, h - self.padding*2)
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
        self._update_cached_surface_if_needed()
        self.game_data.screen.blit(self._cached_surface, self.rect.topleft)
