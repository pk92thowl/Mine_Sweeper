import pygame
import pygame.freetype
from pygame.sprite import Sprite

from game_data import GameData
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
                print("Restart game")
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
