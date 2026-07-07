import pygame
from pathlib import Path

_sounds:dict[str, pygame.mixer.Sound] = {}
_muted = False

def init():
    pygame.mixer.init()
    _sounds["reveal"] = pygame.mixer.Sound(file=Path("assets/sounds/Sand_dig1.ogg"))
    _sounds["explosion"] = pygame.mixer.Sound(Path("assets/sounds/explosion.ogg"))
    _sounds["flag_place"] = pygame.mixer.Sound(Path("assets/sounds/flag.ogg"))
    _sounds["flag_remove"] = pygame.mixer.Sound(Path("assets/sounds/flag2.ogg"))
    _sounds["lose"] = pygame.mixer.Sound(Path("assets/sounds/game-over.ogg"))
    
    _sounds["win"] = pygame.mixer.Sound(Path("assets/sounds/win.ogg"))
    # _sounds["win"] = pygame.mixer.Sound(Path("assets/sounds/fanfare.ogg"))

    # Lautstärke anpassen (0.0 bis 1.0)
    # _sounds["reveal"].set_volume(0.5)
    for soundname in _sounds:
        _sounds[soundname].set_volume(0.5)
    # _sounds["reveal"].set_volume(0.5)


def play(name: str):
    if _muted:
        return
    if name in _sounds:
        _sounds[name].play()
        
def play_reveal():
    play("reveal")
    
def play_explosion():
    play("explosion")
    
def play_flag_place():
    play("flag_place")
    
def play_flag_remove():
    play("flag_remove")
    
def play_win():
    play("win")
    
def play_lose():
    play("lose")
    
    

def toggle_mute() -> bool:
    global _muted
    _muted = not _muted
    return _muted

def is_muted() -> bool:
    return _muted