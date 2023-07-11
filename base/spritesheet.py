import pygame

class SpriteSheet:
    def __init__(self, image) -> None:
        self.sheet = image

    def get_sprite(
            self, 
            frame, 
            width, 
            height, 
            scale, 
            trans_color = (0, 0, 0)
        ) -> pygame.SurfaceType:
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), ((frame * width), 0, width, height))
        image = pygame.transform.scale(image, (width * scale, height * scale))
        
        if trans_color:
            image.set_colorkey(trans_color)

        return image
