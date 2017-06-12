from apps import App, action
import pygame.camera
import pygame.image


class Main(App):
    def __init__(self, name=None, device=None):
        App.__init__(self, name, device)
        pygame.camera.init()
        self.camera = pygame.camera.Camera(pygame.camera.list_cameras()[0])
        self.is_running = False

    @action
    def start(self):
        self.camera.start()
        self.is_running = True

    @action
    def stop(self):
        self.camera.stop()
        self.is_running = False

    @action
    def save_screenshot(self, path):
        if not self.is_running:
            self.camera.start()
            self.is_running = True
        image_surface = self.camera.get_image()
        pygame.image.save(image_surface, path)

    def shutdown(self):
        self.stop()
