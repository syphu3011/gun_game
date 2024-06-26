import random
import pygame
import sys
from utils.network import Network
from models.character import Character
from models.gun import Gun
from models.player import Player
from scenes.lose_screen import LoseScreen  # Import màn hình thua
from scenes.win_screen import WinScreen    # Import màn hình thắng

class PVP:
    def __init__(self, screen, model) -> None:
        network = Network()
        _player_receive = network.getPlayer()
        _playerID = _player_receive.player

        self.screen = screen
        self.model = model
        self.running = True

        _player1 = Character(100, 100, _player_receive.pos, 1, screen, "character1")
        _gun = Gun(_player1, 30)
        _player2 = Character(100, 100, (_player_receive.startEnemyPos, 400), -1, screen, "character2")
        _gun_player2 = Gun(_player2, 30)
    
        _player1.enemy = _player2
        _player2.enemy = _player1
    
        all_sprites = pygame.sprite.Group()
        all_sprites.add(_player1)
        all_sprites.add(_gun)
        all_sprites.add(_player2)
        all_sprites.add(_gun_player2)
    
        MOVE_SPEED = 5  # Giảm tốc độ di chuyển của enemy để không lại quá gần character
        last_shot_time = 0
        last_shot_time_e = 0
        shoot_delay = 500
        reload_time = 4000
        reloaded_time = 0
        reloaded_time_e = 0
        clock = pygame.time.Clock()

        # Tải hình ảnh nền và thay đổi kích thước nếu cần thiết
        background_image = pygame.image.load('res/images/bg.png')
        background_rect = background_image.get_rect()
        pygame.display.set_caption('PVP')
    
        while self.running:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                    self.running = False

            # Kiểm tra trạng thái của nhân vật

            if not _player1.alive():
                # Chuyển sang màn hình thua cuộc
                self.model.current_screen = 'lose'
                all_sprites.empty()
                self.running = False

            elif not _player2.alive():
                # Chuyển sang màn hình thắng
                self.model.current_screen = 'win'
                all_sprites.empty()
                self.running = False

            else:
                screen.blit(background_image, background_rect)

            all_sprites.draw(screen)

            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= MOVE_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += MOVE_SPEED
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                _player1.isJump = True

            isShot = False
            if keys[pygame.K_RETURN] and current_time - last_shot_time > shoot_delay:
                bull = _gun.shoot()
                if bull:
                    isShot = True
                    all_sprites.add(bull)
                last_shot_time = current_time 

            if _gun.current_bull == _gun.max_bull and reloaded_time == 0:
                reloaded_time = current_time
            else:
                if _gun.current_bull == _gun.max_bull and current_time - reloaded_time > reload_time:
                    _gun.current_bull = 0
                    reloaded_time = 0

            if _player1.alive() and _player2.alive():

                # Xử lý nhận data từ enemy - player 2
                player1_send = Player((_player1.rect.x, _player1.rect.y), isShot, _playerID)
                player2_receive = network.send(player1_send)
                
                # Nhận event bắn từ enemy - player 2
                if player2_receive.isShot and current_time - last_shot_time_e > shoot_delay:
                    bull = _gun_player2.shoot()
                    if bull:
                        all_sprites.add(bull)
                    last_shot_time_e = current_time
                if _gun_player2.current_bull == _gun_player2.max_bull and reloaded_time_e == 0:
                    reloaded_time_e = current_time
                else:
                    if _gun_player2.current_bull == _gun_player2.max_bull and current_time - reloaded_time_e > reload_time:
                        _gun_player2.current_bull = 0
                        reloaded_time_e = 0

                # flip
                if (_player1.direct == 1 and _player1.rect.x > _player2.rect.x) or (_player1.direct == -1 and _player1.rect.x <= _player2.rect.x):
                    _player1.flip()
                    _player2.flip()

                # va chạm
                bullets_group = pygame.sprite.Group()
                bullets_group.add(_gun.bullets)
                bullets_group.add(_gun_player2.bullets)
                if len(bullets_group) > 0:
                    hits = pygame.sprite.groupcollide(bullets_group, all_sprites, False, False)
                    for bullet, targets in hits.items():
                        for target in targets:
                            if isinstance(target, Character):
                                if (bullet.gun.character.enemy == target):
                                    target.hp -= bullet.damage
                                    if (target.hp <= 0):
                                        target.kill()
                                    bullet.die()

                dx_e = (player2_receive.pos)[0]
                dy_e = (player2_receive.pos)[1]
                # update
                if all_sprites.has(_player1):
                    if (dx_e > 0 and 750 >_player1.rect.x) or (dx_e < 0 and 0 < _player1.rect.x):
                        _player1.update(dx, dy)
                    else:
                        _player1.update(0, dy)
                if all_sprites.has(_gun):
                    _gun.update()
                
                if all_sprites.has(_player2):
                    if (dx_e > 0 and 750 >_player2.rect.x) or (dx_e < 0 and 0 < _player2.rect.x):
                        _player2.updatePos(dx_e, dy_e)
                    else:
                        _player2.updatePos(0, dy_e)
                if all_sprites.has(_gun_player2):
                    _gun_player2.update()

                _player1.jump()
                _player2.jump()
            else:
                if _player1.alive():
                    _player1.update(0, 0)
                    _gun.update()
                else: 
                    _player2.update(0, 0)
                    _gun_player2.update()

            pygame.display.flip()
            clock.tick(60)