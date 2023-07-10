from collections import namedtuple
import pygame

from base.game import GameAbstractBase

Textures = namedtuple("Textures", ["background", "suits", "numbers", "card", "card_background"])

class SolitareGame(GameAbstractBase):
    game_name = "Solitare"

    def __init__(self) -> None:
        super().__init__()
        pygame.init()
        self.window = pygame.display.set_mode((640, 480))
        pygame.display.set_caption(self.game_name)

    def proccess_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                ...

    def _load_textures(self) -> Textures:
        textures = Textures()

        textures.background
        return textures
