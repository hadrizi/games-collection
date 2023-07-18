import asyncio
import json
import threading
import pygame
import random
import uuid

from websockets.sync.client import connect, ClientConnection

from typing import List, Dict
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
    "card_background",
    "cursor",
    "font"
])

# TODO: create BaseObject class with rect and surface manipulation
#       OR create RectObject class that takes *any* object passed to it and adds rect logic
class CardObject:
    def __init__(self, surface, rect, id) -> None:
        self.surface: pygame.SurfaceType = surface
        self.rect: pygame.Rect = rect
        self.id = id


class PlayerObject:
    def __init__(self, surface, rect) -> None:
        self.surface: pygame.SurfaceType = surface
        self.rect: pygame.Rect = rect


class GameState:
    def __init__(self, cards) -> None:
        self.cards: Dict[str, pygame.SurfaceType] = cards
        self.deck_rect = pygame.Rect(
            10, 10,
            BASE_CARD_SIZE[0] * .4, BASE_CARD_SIZE[1] * .4
        )
        self.cards_on_field: Dict[str, CardObject] = {}
        self.players: Dict[str, PlayerObject] = {}
        self.active_card = None
        self.top_card = None


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

    def __init__(self, ws: ClientConnection) -> None:
        super().__init__()
        pygame.init()
        self.window = pygame.display.set_mode((640, 640))
        pygame.display.set_caption(self.game_name)
        self.textures = self._load_textures()
        self.websocket = ws
        self.player_id = uuid.uuid4()
        self.websocket.send(json.dumps({"type": "init", "player_id": str(self.player_id)}))

        cards = {}
        number_map = {
            10: "J",
            11: "K",
            12: "Q",
            13: "A"
        }
        for suit in ["hearts", "diamonds", "clubs", "spades"]:
            for number in range(1, len(self.textures.red_numbers)):
                card = self._build_card(suit, number)
                cards[f"{suit}_{number+1 if number < 10 else number_map[number]}"] = card
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

                for card in self.game_state.cards_on_field.values():
                    if card.rect.collidepoint(event.pos):
                        self.game_state.active_card = card
                
                if self.game_state.active_card:
                    continue
                
                if self.game_state.deck_rect.collidepoint(event.pos):
                    self.game_state.cards_on_field[self.game_state.top_card[1]] = (
                        CardObject(self.game_state.top_card[0].copy(), self.game_state.deck_rect.copy(), self.game_state.top_card[1]))
                    self.game_state.active_card = self.game_state.cards_on_field[self.game_state.top_card[1]]
                    self.websocket.send(json.dumps({
                        "type": "card_draw",
                        "card": self.game_state.top_card[1]
                    }))


            if event.type == pygame.MOUSEBUTTONUP:
                if not event.button == 1:
                    continue
                    
                self.game_state.active_card = None

            if event.type == pygame.MOUSEMOTION:
                self.websocket.send(json.dumps({
                    "type": "mouse_move", 
                    "pos": event.pos, 
                    "player_id": str(self.player_id)
                }))

                if not self.game_state.active_card:
                    continue

                self.game_state.active_card.rect.move_ip(event.rel)
                self.websocket.send(json.dumps({
                    "type": "card_move",
                    "pos": (self.game_state.active_card.rect.x, self.game_state.active_card.rect.y),
                    "card": self.game_state.active_card.id
                }))
   
    def update(self):
        ...

    def render(self):
        self.window.fill(self.textures.background)
        if self.game_state.top_card:
            self.window.blit(
                self.game_state.top_card[0], 
                (self.game_state.deck_rect.x, self.game_state.deck_rect.y)
            )
        
        for card in self.game_state.cards_on_field.values():
            self.window.blit(card.surface, (card.rect.x, card.rect.y))

        for player in self.game_state.players.values():
            self.window.blit(player.surface, (player.rect.x, player.rect.y))

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
        cursor_image = (
            pygame.image.load('assets/cursor.png').convert_alpha())
        cursor_sheet = SpriteSheet(cursor_image)

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
            font=pygame.font.Font(None, 20),
            cursor=cursor_sheet.get_sprite(0, 48, 48, .4),
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


def accept_ws_messages(game: SolitareGame):
    for message in game.websocket:
        event = json.loads(message)
        
        if event["type"] == "top_card":
            game.game_state.top_card = (game.game_state.cards[event["card"]], event["card"])
        
        if event["type"] == "joined":
            cursor_surface: pygame.SurfaceType = game.textures.cursor.copy()
            player_text = game.textures.font.render(event["player_id"], False, (0,0,0))
            
            player_surface = pygame.Surface(
                (player_text.get_width(), player_text.get_height() + cursor_surface.get_height()),
                pygame.SRCALPHA
            )
            player_surface.blit(cursor_surface, (0, 0))
            player_surface.blit(player_text, (cursor_surface.get_width()+5, 0))
            
            game.game_state.players[event["player_id"]] = PlayerObject(
                player_surface,
                game.game_state.deck_rect.copy()
            )

        if event["type"] == "players":
            for player_id in event["players"]:
                cursor_surface: pygame.SurfaceType = game.textures.cursor.copy()
                player_text = game.textures.font.render(player_id, False, (0,0,0))
                
                player_surface = pygame.Surface(
                    (player_text.get_width(), player_text.get_height() + cursor_surface.get_height()),
                    pygame.SRCALPHA
                )
                player_surface.blit(cursor_surface, (0, 0))
                player_surface.blit(player_text, (cursor_surface.get_width()+5, 0))

                game.game_state.players[player_id] = PlayerObject(
                    player_surface,
                    game.game_state.deck_rect.copy()
                )

        if event["type"] == "mouse_move":
            try:
                game.game_state.players[event["player_id"]].rect.move_ip(
                    event["pos"][0] - game.game_state.players[event["player_id"]].rect.x,
                    event["pos"][1] - game.game_state.players[event["player_id"]].rect.y,
                )
            except KeyError:
                pass
        
        if event["type"] == "card_move":
            game.game_state.cards_on_field[event["card"]].rect.move_ip(
                event["pos"][0] - game.game_state.cards_on_field[event["card"]].rect.x,
                event["pos"][1] - game.game_state.cards_on_field[event["card"]].rect.y,
            )

        if event["type"] == "card_draw":
            game.game_state.cards_on_field[event["card"]] = (
                CardObject(game.game_state.cards[event["card"]], game.game_state.deck_rect.copy(), event["card"]))


def main():
    with connect("ws://localhost:8001") as websocket:
        game = SolitareGame(websocket)
        game_thread = threading.Thread(target=game.run)
        ws_thread = threading.Thread(target=accept_ws_messages, args=(game, ))

        game_thread.start()
        ws_thread.start()

        game_thread.join()
        ws_thread.join()


if __name__ == "__main__":
    main()
