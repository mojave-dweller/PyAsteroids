import pygame
import sys
import math
import random

# Set up our environments
pygame.init()
pygame.mixer.init()

# Create screen, create colors, create fonts, load background image
aspectW = 16
aspectH = 9
aspectR = 60
width, height = aspectW*aspectR,aspectH*aspectR
xNormal, yNormal = width/2, height/2
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Py-Asteroids")
white = (255, 255, 255)
black = (0, 0, 0)
font = pygame.font.Font(None, 25)
pauseFont = pygame.font.Font(None, 70)
subFont = pygame.font.Font(None, 30)
controlsFont = pygame.font.Font(None, 20)
background = pygame.image.load("StarryBackground.png").convert()

# Load our game sounds
# Create a channel for the ambient space sound so that we can pause at times
asteroidCollisionSound = pygame.mixer.Sound("AsteroidHit.wav")
crashSound = pygame.mixer.Sound("DeathSound.wav")
levelUpSound = pygame.mixer.Sound("LevelUp.wav")
spaceAmbientSound = pygame.mixer.Sound("Space.wav")
backgroundChannel = spaceAmbientSound.play(-1)
backgroundChannel.pause()
startUpSound = pygame.mixer.Sound("Startup.wav")
startUpSound.set_volume(0.25)
shootSound = pygame.mixer.Sound("Laser.wav")

# Movement variables for background image
offsetX = 0
offsetY = 0
movementSpeed = 0.5
movementRange = 10 

# Create sprite groups
playerSprite = pygame.sprite.GroupSingle()
shootSprites = pygame.sprite.Group()
asteroidSprites = pygame.sprite.Group()
deadAsteroidSprites = pygame.sprite.Group()

# Create array of pictures
asteroids = []
for i in range(7):
    asteroids.append(f'Asteroid{i+1}.png')

# Our player sprite. Constructs with image, x, and y
class PlayerSprite(pygame.sprite.Sprite):
    def __init__(self, imagePath, x, y):
        super().__init__()
        self.originalImage = pygame.image.load(imagePath).convert_alpha()
        self.image = self.originalImage
        self.image.set_colorkey(black)
        self.rect = self.image.get_rect(center = (x, y))

        # Set up our direction, position, angle for rotation, and checks for movement
        self.direction = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(x, y)
        self.angle = 0
        self.moveForward = False
        self.moveBackward = False
        self.rotateLeft = False
        self.rotateRight = False

        # An animation for a crashed ship
        self.dying = False
        self.timer = 0

    # Handle movement, position, and screen bounds
    def update(self):
        if self.rotateLeft:
            self.angle += 6
        if self.rotateRight:
            self.angle -= 6
        self.angle %= 360
        angle_rad = math.radians(self.angle)
        self.direction = pygame.math.Vector2(-math.sin(angle_rad),-math.cos(angle_rad))
        if self.moveForward:
            self.position += self.direction*5
        if self.moveBackward:
            self.position -= self.direction*5
        self.rect.center = (round(self.position.x), round(self.position.y))
        if self.rect.left < 0: 
            self.rect.left = 0
            self.position.x = self.rect.centerx
        if self.rect.right > width: 
            self.rect.right = width
            self.position.x = self.rect.centerx
        if self.rect.top < 0: 
            self.rect.top = 0
            self.position.y = self.rect.centery
        if self.rect.bottom > height: 
            self.rect.bottom = height
            self.position.y = self.rect.centery

        self.rotate()
        if self.dying:
            self.timer += 1
        if self.timer == 10:
            pygame.sprite.Sprite.kill(self)

    def rotate(self):
        center = self.rect.center
        self.image = pygame.transform.rotate(self.originalImage, self.angle)
        self.rect = self.image.get_rect(center=center)
        
    # Upon calling shoot, a sprite of the ShootSprite class will be called
    def shoot(self):
        shoot = ShootSprite("ShootSprite.png", self.position.x, self.position.y, shootSprites, self.direction, self.angle)
        shootSound.play()

    def handleCollision(self):
        self.originalImage = pygame.image.load("AsteroidDestroy.png").convert()
        self.dying = True
        crashSound.play()
        

# Our Asteroid class. Constructs with an image, x, y, and a variable called modifier that will dictate extra behavior in the class
class AsteroidSprite(pygame.sprite.Sprite):
    def __init__(self, image_path, x, y, modifier):
        super().__init__()
        self.image = pygame.image.load(image_path).convert()
        self.image.set_colorkey(black)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Modifier dictates speed of asteroid and scale of asteroid
        self.speed = random.randint(1, modifier+1)
        self.scale = random.randint(1, modifier+1) * .5
        if self.scale <= 1:
            self.scale = 1
        if self.scale >= 7:
            self.scale = 7
        self.imageSize = self.image.get_size()
        self.newImageWidth = self.imageSize[0] * self.scale
        self.newImageHeight = self.imageSize[1] * self.scale
        self.image = pygame.transform.scale(self.image, (self.newImageWidth, self.newImageHeight))
        self.rect = self.image.get_rect()
        if x > width:
            directionX = -1 + -self.speed/3
        else:
            directionX = 1 + self.speed/3
        if y > height:
            directionY = -1 + -self.speed/3
        else:
            directionY = 1 + self.speed/3
        self.direction = pygame.math.Vector2(directionX, directionY)
        self.position = pygame.math.Vector2(x, y)

    # Handle position, movement, and boundary checking
    def update(self):
        self.position.x += self.direction.x + random.randint(-1, 1)
        self.position.y += self.direction.y + random.randint(-1, 1)
        self.rect.center = (round(self.position.x), round(self.position.y))
        if self.rect.left < -100: 
            pygame.sprite.Sprite.kill(self)
        if self.rect.right > width+100: 
            pygame.sprite.Sprite.kill(self)
        if self.rect.top < -100: 
            pygame.sprite.Sprite.kill(self)
        if self.rect.bottom > height+100: 
            pygame.sprite.Sprite.kill(self)

    # When an asteroid collides with a shoot sprite, the asteroid will be removed from the group and call a DeadAsteroid sprite for a period of time,
    # keeping the size of the original scale of the asteroid when originally constructed, but losing collision with player and disappearing after 10 ticks
    def handleCollision(self):
        death = DeadAsteroid(self.position.x, self.position.y, deadAsteroidSprites, self.scale)
        pygame.sprite.Sprite.kill(self)
        asteroidCollisionSound.play()

# DeadAsteroid class. Replaces an asteroid that has been shot to separate collisions from a non-shot asteroid and the player
# The arguments are taken from the asteroid that called it, keeping in line with the original size and location
class DeadAsteroid(pygame.sprite.Sprite):
    def __init__(self, x, y, group, scale):
        super().__init__()
        self.image = pygame.image.load("AsteroidDestroy.png").convert()
        self.image.set_colorkey(black)
        self.imageSize = self.image.get_size()
        self.newImageWidth = self.imageSize[0] * scale
        self.newImageHeight = self.imageSize[1] * scale
        self.image = pygame.transform.scale(self.image, (self.newImageWidth, self.newImageHeight))
        self.position = pygame.math.Vector2(x, y)
        self.imageSize = self.image.get_size()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.timer = 0
        group.add(self)

    # The only purpose of this sprite is to create a shot asteroid sprite, meaning it disappears after a small time
    def update(self):
        self.rect.center = (round(self.position.x), round(self.position.y))
        self.timer += 1
        if self.timer == 10:
            pygame.sprite.Sprite.kill(self)
                
# Our Shoot sprite. Constructs with an image, x, y, the group it will belong to (as it is called by another sprite)
# direction, and angle. Direction and angle are determined by the player's sprite forward face
class ShootSprite(pygame.sprite.Sprite):
    def __init__(self, imagePath, x, y, group, direction, angle):
        super().__init__()
        self.originalImage = pygame.image.load(imagePath).convert_alpha()
        self.image = self.originalImage
        self.image.set_colorkey(black)
        self.rect = self.image.get_rect(center = (x, y))
        self.movement = direction
        self.position = pygame.math.Vector2(x, y)
        self.angle = angle
        self.destroy = False
        
        group.add(self)

    # Handle position, movement, and boundary checking
    def update(self):
        self.position += self.movement*10
        self.rect.center = (round(self.position.x), round(self.position.y))
        if self.rect.left < 0: 
            pygame.sprite.Sprite.kill(self)
        if self.rect.right > width: 
            pygame.sprite.Sprite.kill(self)
        if self.rect.top < 0: 
            pygame.sprite.Sprite.kill(self)
        if self.rect.bottom > height: 
            pygame.sprite.Sprite.kill(self)
        self.rotate()
        if self.destroy: 
            pygame.sprite.Sprite.kill(self)

    def rotate(self):
        center = self.rect.center
        self.image = pygame.transform.rotate(self.originalImage, self.angle)
        self.rect = self.image.get_rect(center=center)

    # Useless function that requires creation so Asteroid animation can function
    def handleCollision(self):
        return None

# Create the player
player = PlayerSprite("PlayerSprite.png", xNormal, yNormal+75)
playerSprite.add(player)

# Time variables. All variables are tied to delta time in order to normalize time
clock = pygame.time.Clock()
running = True
timeTickAdd = 0
secondTick = 0
timeLeft = 0
startUpTimer = 0

# Gameplay variables. Score accumulates for shoot/asteroid collisions. levelCount and levelIncrement
# affect level progression. asteroidCount helps determine frequency of asteroid spawns. paused and youLose
# are gameplay buffers, where paused acts as it sounds, and youLose ends the loop.
score = 0
levelCount = 0
levelTimeModifier = 1-levelCount*0.05
levelIncrement = False
asteroidCount = 1
paused = False
youLose = False

# Game loop
while running:
    dt = clock.tick(60) / 1000.0  # Delta time in seconds for the background
    startUpTimer += dt
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                player.moveForward = True
            if event.key == pygame.K_a:
                player.rotateLeft = True
            if event.key == pygame.K_s:
                player.moveBackward = True
            if event.key == pygame.K_d:
                player.rotateRight = True
            if event.key == pygame.K_SPACE:
                player.shoot()
            if event.key == pygame.K_p:
                if not youLose: # Game cannot be unpaused if game has been lost
                    paused = not paused
            if event.key == pygame.K_y:
                if youLose:
                    startUpTimer = 0
                    secondTickAdd = 0
                    levelTimeModifier = 1.0
                    levelCount = 0
                    score = 0
                    levelIncrement = True
                    youLose = not youLose
                    paused = False
                    player = PlayerSprite("PlayerSprite.png", xNormal, yNormal+75)
                    playerSprite.add(player)
                    asteroidSprites.empty()
                    shootSprites.empty()
            if event.key == pygame.K_n:
                if youLose or paused:
                    running = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                player.moveForward = False
            if event.key == pygame.K_a:
                player.rotateLeft = False
            if event.key == pygame.K_s:
                player.moveBackward = False
            if event.key == pygame.K_d:
                player.rotateRight = False

    screen.fill(black)
    offsetX = math.sin(startUpTimer * 0.7) * movementRange
    offsetY = math.sin(startUpTimer * 0.5) * movementRange
    screen.blit(background, (offsetX, offsetY))

    # Startup screen, about 5 seconds
    if startUpTimer <= 5:
        backgroundChannel.pause()
        startUpSound.play()
        startScreen = pauseFont.render("Asteroids Clone", False, white)
        startScreenSub = subFont.render("Get Ready...", False, white)
        screen.blit(startScreen, (xNormal-180, yNormal-50))
        screen.blit(startScreenSub, (xNormal-60, yNormal+15))

    # Pause and Lose messages -- once again, game cannot be unpaused if lost
    if paused:
        if not youLose and startUpTimer >= 5:
            pauseText = pauseFont.render("Paused", False, white)
            exitText = subFont.render("Press N to exit.", False, white)
            screen.blit(pauseText, (xNormal-90, yNormal-15))
            screen.blit(exitText, (xNormal-80, yNormal+35))
        elif youLose:
            loseText = pauseFont.render("You Lose!", False, white)
            finalScoreText = subFont.render(f'Final Score: {score}', False, white)
            replayText = font.render("Press Y to replay, or N to exit.", False, white)
            screen.blit(loseText, (xNormal-120, yNormal-30))
            screen.blit(finalScoreText, (xNormal-85, yNormal+30))
            screen.blit(replayText, (xNormal-130, height-30))

    # Main gameplay logic
    if not paused and startUpTimer >= 5 and not youLose:
        backgroundChannel.unpause()

        # When we increment levels, we will decrease the time it takes for the level to increment
        if levelIncrement:
            levelUpSound.play()
            levelCount += 1
            timeLeft = 60*levelTimeModifier
            if (timeLeft <= 30):
                timeLeft = 30
            levelTimeModifier = 1-levelCount*0.05
            timeTickAdd = 0
            levelIncrement = False

        # Calculate seconds remaining
        secondTick = timeLeft-timeTickAdd
        # If time is remaining before next level...
        if (timeTickAdd <= timeLeft):
            # This results in a number that is used for asteroid spawn frequency, capped at 30
            asteroidCount = levelCount*3
            if (asteroidCount >= 30):
                asteroidCount = 30
            # Random number between 0 and 1000 for spawn chance
            asteroidChance = random.randint(0, 1000)

            # If the random number is less than or equal to the asteroidCount cap, spawn an asteroid
            if (asteroidChance <= asteroidCount):
                
                # Asteroids are given a random location outside of the screen. This is determined by
                # deciding if the x location is left or right of the screen, and if y is above or below
                # the screen, and then determining a random location within those confines
                spawnXBool = random.randint(0, 1)
                spawnYBool = random.randint(0, 1)
                if spawnXBool:
                    spawnX = random.randint(width, width+25)
                else:
                    spawnX = random.randint(-25, -1)
                if spawnYBool:
                    spawnY = random.randint(height, height+25)
                else:
                    spawnY = random.randint(-25, -1)

                # Once we have our location, an asteroid will be spawned with a random asteroid image,
                # the positions we calculated, and the levelCount as the modifier, and then we finally
                # add it to the asteroidSprites group
                asteroid = AsteroidSprite(asteroids[random.randint(0, 6)], spawnX, spawnY, levelCount)
                asteroidSprites.add(asteroid)

        # Calculate collisions. For each shoot sprite spawned, check collisison with Asteroids
        # When they collide, the asteroid will handle the collision within its class, whereas
        # the shoot sprite will be destroyed immediately, and then finally increment the score
        for shoot in shootSprites:
            collidedSprites = pygame.sprite.spritecollide(shoot, asteroidSprites, False)
            for sprite in collidedSprites:
                sprite.handleCollision()
                shoot.kill()
                score += 15

        # This time, calculate collisions between player and asteroid.
        for player in playerSprite:
            collidedSprites = pygame.sprite.spritecollide(player, asteroidSprites, False)
            for sprite in collidedSprites:
                sprite.handleCollision()
                player.handleCollision()

        # Update all of our sprites once everything is calculated
        playerSprite.update()
        shootSprites.update()
        asteroidSprites.update()
        deadAsteroidSprites.update()

        # Increment the level when the timer runs out, and end game if the player collides with an asteroid
        timeTickAdd += dt
        if (secondTick <= 0):
            levelIncrement = True
        if not (pygame.sprite.Sprite.alive(player)):
            youLose = True
            paused = True

    # Always draw the sprites and UI, even when paused, but not when game is lost
    if not youLose and startUpTimer >= 5:
        # UI
        # Level Count
        if not levelIncrement:
            
            levelText = font.render(f'Level: {levelCount}', False, white)
            screen.blit(levelText, (15, 15))

        # Time remaining
        timeRemaining = font.render(f'Time Remaining: {secondTick:.0f} seconds', False, white)
        screen.blit(timeRemaining, (xNormal-130, 15))

        # Score Count
        scoreText = font.render(f'Score: {score}', False, white)
        screen.blit(scoreText, (xNormal+275, 15))

        # Control UI - Indicate what keys do what
        forwardBackwardText = controlsFont.render(f'W, S = Forward, Backward', False, white)
        screen.blit(forwardBackwardText, (10, height-20))
            
        rotateText = controlsFont.render(f'A, D = Rotate Left, Rotate Right', False, white)
        screen.blit(rotateText, (xNormal-150, height-20))
            
        shootText = controlsFont.render(f'Spacebar = Shoot', False, white)
        screen.blit(shootText, (xNormal+90, height-20))
            
        pressPauseText = controlsFont.render(f'P = Pause', False, white)
        screen.blit(pressPauseText, (width-80, height-20))
        
        playerSprite.draw(screen)
        asteroidSprites.draw(screen)
        shootSprites.draw(screen)
        deadAsteroidSprites.draw(screen)
    pygame.display.flip()
    
pygame.quit()
sys.exit()
