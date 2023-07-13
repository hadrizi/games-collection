import pygame
import random

from typing import List
from collections import namedtuple

from base.game import GameAbstractBase
from base.spritesheet import SpriteSheet

BASE_CARD_ROUNDNESS = 20
BASE_CARD_BORDER = 7
BASE_CARD_SIZE = (256, 490)
BASE_CARD_SIZE_MINIMIZED = (BASE_CARD_SIZE[0] * .4, BASE_CARD_SIZE[1] * .4)

Textures = namedtuple("Textures", [
    "background", 
    "suits", 
    "suits_minimized", 
    "black_numbers", 
    "red_numbers", 
    "card", 
    "card_background"
])

# TODO: create BaseObject class with rect and surface manipulation
#       OR create RectObject class that takes *any* object passed to it and adds rect logic
class CardObject:
    def __init__(self, surface, rect) -> None:
        self.surface: pygame.SurfaceType = surface
        self.rect: pygame.Rect = rect


class GameState:
    def __init__(self, cards) -> None:
        self.cards: List[pygame.SurfaceType] = cards
        self.deck = self.cards.copy() # TODO: deck should have its own object class
        self.deck_rect = pygame.Rect(
            10, 10,
            BASE_CARD_SIZE[0] * .4, BASE_CARD_SIZE[1] * .4
        )
        self.cards_on_field: List[CardObject] = []
        self.active_card = None
        self.shuffle_deck()

    def shuffle_deck(self):
        random.shuffle(self.deck)


class SolitareGame(GameAbstractBase):
    game_name = "Solitare"

    card_coords = {
        "upper_left_number_denomination": (17, 16),
        "upper_left_suit_denomination": (23, 70),
        "down_right_number_denomination": (192, 431),
        "down_right_suit_denomination": (199, 391),
        "upper_middle_suit": (104, 56),
        "down_middle_suit": (104, 376),
        "center_middle_suit": (104, 216),
        "upper_left_suit": (64, 56),
        "upper_right_suit": (144, 56),
        "down_left_suit": (64, 376),
        "down_right_suit": (144, 376),
        "center_left_suit": (64 ,216),
        "center_right_suit": (144 ,216),
        "highhalf_middle_suit": (104, 136),
        "highhalf_left_suit": (64, 144),
        "highhalf_right_suit": (144, 144),
        "lowhalf_left_suit": (64, 288),
        "lowhalf_right_suit": (144, 288),
    }

    card_templates = [
        (),
        ("upper_middle_suit", "down_middle_suit"), # 2
        ("upper_middle_suit", "down_middle_suit", "center_middle_suit"), # 3
        ("upper_left_suit", "upper_right_suit", "down_left_suit", "down_right_suit"), # 4
        ("upper_left_suit", "upper_right_suit", "down_left_suit", "down_right_suit", "center_middle_suit"), # 5
        ("upper_left_suit", "upper_right_suit", "down_left_suit", "down_right_suit", "center_left_suit", "center_right_suit"), # 6
        ("upper_left_suit", "upper_right_suit", "down_left_suit", "down_right_suit", "center_left_suit", "center_right_suit", "highhalf_middle_suit"), # 7
        ("upper_left_suit", "upper_right_suit", "down_left_suit", "down_right_suit", "highhalf_left_suit", "highhalf_right_suit", "lowhalf_left_suit", "lowhalf_right_suit"), # 8
        ("upper_left_suit", "upper_right_suit", "down_left_suit", "down_right_suit", "highhalf_left_suit", "highhalf_right_suit", "lowhalf_left_suit", "lowhalf_right_suit", "center_middle_suit"), # 9
        ("upper_left_suit", "upper_right_suit", "down_left_suit", "down_right_suit", "highhalf_left_suit", "highhalf_right_suit", "lowhalf_left_suit", "lowhalf_right_suit", "center_left_suit", "center_right_suit"), # 10
        (), # J
        (), # Q
        (), # K
        ("center_middle_suit", ), # A
    ]

    def __init__(self) -> None:
        super().__init__()
        pygame.init()
        self.window = pygame.display.set_mode((640, 640))
        pygame.display.set_caption(self.game_name)
        self.textures = self._load_textures()

        cards = []
        for suit in ["hearts", "diamonds", "clubs", "spades"]:
            for number in range(1, len(self.textures.red_numbers)):
                card = self._build_card(suit, number)
                cards.append(card)
        self.game_state = GameState(cards)

    # TODO: all this if mess should be turned into different event maps
    def proccess_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not event.button == 1:
                    continue

                for card in self.game_state.cards_on_field:
                    if card.rect.collidepoint(event.pos):
                        self.game_state.active_card = card
                
                if self.game_state.active_card:
                    continue
                
                if self.game_state.deck_rect.collidepoint(event.pos) and self.game_state.deck:
                    card_surface = self.game_state.deck.pop()
                    self.game_state.cards_on_field.append(
                        CardObject(card_surface, self.game_state.deck_rect.copy()))
                    self.game_state.active_card = self.game_state.cards_on_field[-1]


            if event.type == pygame.MOUSEBUTTONUP:
                if not event.button == 1:
                    continue
                    
                self.game_state.active_card = None

            if event.type == pygame.MOUSEMOTION:
                if not self.game_state.active_card:
                    continue

                self.game_state.active_card.rect.move_ip(event.rel)
                    

    def update(self):
        ...

    def render(self):
        self.window.fill(self.textures.background)
        if self.game_state.deck:
            self.window.blit(
                self.game_state.deck[-1], 
                (self.game_state.deck_rect.x, self.game_state.deck_rect.y)
            )
        
        for card in self.game_state.cards_on_field:
            self.window.blit(card.surface, (card.rect.x, card.rect.y))

        pygame.display.update()

    def _build_card(self, suit, number) -> pygame.SurfaceType:
        card_base: pygame.SurfaceType = self.textures.card.copy()
        
        mini_suit_tex = self.textures.suits_minimized[suit]
        suit_tex = self.textures.suits[suit]
        if suit in ["hearts", "diamonds"]:
            number_tex = self.textures.red_numbers[number]
        else:
            number_tex = self.textures.black_numbers[number]
        
        # denominations
        card_base.blit(
            number_tex, 
            self.card_coords["upper_left_number_denomination"]
        )
        card_base.blit(
            pygame.transform.flip(number_tex, False, True).convert_alpha(), 
            self.card_coords["down_right_number_denomination"]
        )
        card_base.blit(
            mini_suit_tex, 
            self.card_coords["upper_left_suit_denomination"]
        )
        card_base.blit(
            mini_suit_tex, 
            self.card_coords["down_right_suit_denomination"]
        )

        # suits
        for coord_alias in self.card_templates[number]:
            card_base.blit(suit_tex, self.card_coords[coord_alias])

        return pygame.transform.scale(card_base, BASE_CARD_SIZE_MINIMIZED)

    def _load_textures(self) -> Textures:
        sprite_sheet_image = (
            pygame.image.load('assets/card-numbers-sheet.png').convert_alpha())
        sprite_sheet = SpriteSheet(sprite_sheet_image)

        card = pygame.Surface(BASE_CARD_SIZE).convert_alpha()
        card.fill((255, 255, 255))
        card.set_colorkey((0, 0, 0))

        card_background = card.copy()
        card_background.fill((75, 58, 38)) 
        
        # XXX: pretty weird way to set border color and border radius for card
        card_size = card.get_size()
        round_rect = pygame.Surface(card_size, pygame.SRCALPHA)
        pygame.draw.rect(
            round_rect, 
            (255, 255, 255), 
            (0, 0, *card_size),
            border_radius=BASE_CARD_ROUNDNESS,
        )
        pygame.draw.rect(
            round_rect, 
            pygame.Color("Grey"), 
            (0, 0, *card_size),
            border_radius=BASE_CARD_ROUNDNESS,
            width=BASE_CARD_BORDER
        )
        card.blit(round_rect, (0, 0), None, pygame.BLEND_RGBA_MIN)
        card_background.blit(round_rect, (0, 0), None, pygame.BLEND_RGBA_MIN)

        return Textures(
            background=(51, 165, 49),
            card=card,
            card_background=card_background,
            suits = {
                "hearts":   sprite_sheet.get_sprite(0, 48, 48, 1),
                "diamonds": sprite_sheet.get_sprite(1, 48, 48, 1),
                "clubs":    sprite_sheet.get_sprite(2, 48, 48, 1),
                "spades":   sprite_sheet.get_sprite(3, 48, 48, 1),
            },
            suits_minimized = {
                "hearts":   sprite_sheet.get_sprite(0, 48, 48, .7),
                "diamonds": sprite_sheet.get_sprite(1, 48, 48, .7),
                "clubs":    sprite_sheet.get_sprite(2, 48, 48, .7),
                "spades":   sprite_sheet.get_sprite(3, 48, 48, .7),
            },
            black_numbers = [
                sprite_sheet.get_sprite(4,  48, 48, 1),
                sprite_sheet.get_sprite(5,  48, 48, 1),
                sprite_sheet.get_sprite(6,  48, 48, 1),
                sprite_sheet.get_sprite(7,  48, 48, 1),
                sprite_sheet.get_sprite(8,  48, 48, 1),
                sprite_sheet.get_sprite(9,  48, 48, 1),
                sprite_sheet.get_sprite(10, 48, 48, 1),
                sprite_sheet.get_sprite(11, 48, 48, 1),
                sprite_sheet.get_sprite(12, 48, 48, 1),
                sprite_sheet.get_sprite(13, 48, 48, 1),
                sprite_sheet.get_sprite(24, 48, 48, 1),
                sprite_sheet.get_sprite(25, 48, 48, 1),
                sprite_sheet.get_sprite(26, 48, 48, 1),
                sprite_sheet.get_sprite(27, 48, 48, 1),
            ],
            red_numbers = [
                sprite_sheet.get_sprite(14,  48, 48, 1),
                sprite_sheet.get_sprite(15,  48, 48, 1),
                sprite_sheet.get_sprite(16,  48, 48, 1),
                sprite_sheet.get_sprite(17,  48, 48, 1),
                sprite_sheet.get_sprite(18,  48, 48, 1),
                sprite_sheet.get_sprite(19,  48, 48, 1),
                sprite_sheet.get_sprite(20, 48, 48, 1),
                sprite_sheet.get_sprite(21, 48, 48, 1),
                sprite_sheet.get_sprite(22, 48, 48, 1),
                sprite_sheet.get_sprite(23, 48, 48, 1),
                sprite_sheet.get_sprite(28, 48, 48, 1),
                sprite_sheet.get_sprite(29, 48, 48, 1),
                sprite_sheet.get_sprite(30, 48, 48, 1),
                sprite_sheet.get_sprite(31, 48, 48, 1),
            ]
        )


def main():
    game = SolitareGame()
    game.run()


if __name__ == "__main__":
    main()
