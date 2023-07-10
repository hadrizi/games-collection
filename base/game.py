import pygame
from abc import ABC, abstractmethod

class GameAbstractBase(ABC):
    @abstractmethod
    def __init__(self) -> None:
        self.running = True
        self.clock = pygame.time.Clock()

    @abstractmethod
    def proccess_input(self):
        ...

    @abstractmethod
    def proccess_mouse_input(self):
        ...

    @abstractmethod
    def update(self):
        ...

    @abstractmethod
    def render(self):
        ...

    def run(self):
        while self.running:
            self.proccess_input()
            self.update()
            self.render()
            self.clock.tick(60)