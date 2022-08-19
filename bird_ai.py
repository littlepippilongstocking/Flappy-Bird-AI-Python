"""
Dilyana Koleva, August 2022
The classic flappy bird game made with Python and PyGame
"""
import pygame
import neat
import time
import os
import random

pygame.font.init()

width = 600
height = 650
window = pygame.display.set_mode((width, height))

bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird" + str(x) + ".png"))) for x in
               range(1, 4)]
pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")).convert_alpha())
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "bg.png")).convert_alpha(), (600, 750))

stat_font = pygame.font.SysFont("comicsans", 50)


class Bird:
    images = bird_images
    # How much the bird is going to tilt
    max_rotation = 25
    # How much to rotate at each frame
    rotation_velocity = 20
    # How long to show each bird animation
    animation_time = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0

        self.velocity = 0
        self.height = self.y
        self.image_count = 0
        self.image = self.images[0]

    def jump(self):
        self.velocity = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        # for downward acceleration
        displacement = self.velocity * self.tick_count + 0.5 * 3 * self.tick_count ** 2
        if displacement >= 16:
            displacement = (displacement / abs(displacement)) * 16
        elif displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        # tilt up
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.max_rotation:
                self.tilt = self.max_rotation
        # tilt down
        else:
            if self.tilt > -90:
                self.tilt -= self.rotation_velocity

    def draw(self, window):
        # Check what image to show based on the image count
        self.image_count += 1

        if self.image_count <= self.animation_time:
            self.image = self.images[0]
        elif self.image_count <= self.animation_time * 2:
            self.image = self.images[1]
        elif self.image_count <= self.animation_time * 3:
            self.image = self.images[2]
        elif self.image_count <= self.animation_time * 4:
            self.image = self.images[1]
        elif self.image_count == self.animation_time * 4 + 1:
            self.image = self.images[0]
            self.image_count = 0

        # so when bird is nose diving it isn't flapping
        if self.tilt <= -80:
            self.image = self.images[1]
            self.image_count = self.animation_time * 2

        rotated_image = pygame.transform.rotate(self.image, self.tilt)
        new_rect = rotated_image.get_rect(center=self.image.get_rect(topleft=(self.x, self.y)).center)
        window.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.image)


class Pipe:
    gap = 200
    velocity = 5

    def __init__(self, x):
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0
        self.bottom = 0

        self.pipe_top = pygame.transform.flip(pipe_img, False, True)
        self.pipe_bottom = pipe_img

        self.passed = False

        self.set_height()

    # Sets the top and bottom of the pipe
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.pipe_top.get_height()
        self.bottom = self.height + self.gap

    def move(self):
        # Simply move the pipe to the left
        self.x -= self.velocity

    def draw(self, window):
        window.blit(self.pipe_top, (self.x, self.top))
        window.blit(self.pipe_bottom, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.pipe_top)
        bottom_mask = pygame.mask.from_surface(self.pipe_bottom)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True

        return False


class Base:
    velocity = 5
    width = base_img.get_width()
    image = base_img

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.width

    #  move floor so it looks like its scrolling
    def move(self):
        self.x1 -= self.velocity
        self.x2 -= self.velocity

        # Check if image is off-screen and circle it back
        if self.x1 + self.width < 0:
            self.x1 = self.x2 + self.width

        if self.x2 + self.width < 0:
            self.x2 = self.x1 + self.width

    # Draw the floor. This is two images that move together.
    def draw(self, window):
        window.blit(self.image, (self.x1, self.y))
        window.blit(self.image, (self.x2, self.y))


def draw_window(window, birds, pipes, base, score):
    window.blit(bg_img, (0, 0))

    for pipe in pipes:
        pipe.draw(window)

    base.draw(window)

    for bird in birds:
        bird.draw(window)

    text = stat_font.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(text, (width - 10 - text.get_width(), 10))

    pygame.display.update()


def main(genomes, config):
    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(570)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            # determine whether to use the first or second pipe
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].pipe_top.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        # give each bird a fitness of 0.1 for each frame it stays alive
        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[birds.index(bird)].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        base.move()

        add_pipe = False
        removed = []

        for pipe in pipes:
            pipe.move()
            # check for collision
            for bird in birds:
                if pipe.collide(bird):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.pipe_top.get_width() < 0:
                removed.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

            # pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5

            pipes.append(Pipe(width))

        for r in removed:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.image.get_height() - 10 >= 730 or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(window, birds, pipes, base, score)


# runs the NEAT algorithm to train a neural network to play flappy bird
def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Create the population
    population = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    # Run for up to 50 generations.
    winner = population.run(main, 50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
