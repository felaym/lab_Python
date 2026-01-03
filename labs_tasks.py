import random
from typing import List, Optional
import sys
import tty
import termios
import os


def read_single_keypress():
    file_descriptor = sys.stdin.fileno()
    original_terminal_settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setraw(sys.stdin.fileno())
        pressed_key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, original_terminal_settings)
    return pressed_key


MOVEMENT_KEYS = {
    'w': (-1, 0), 'ц': (-1, 0),
    's': (1, 0), 'і': (1, 0),
    'a': (0, -1), 'ф': (0, -1),
    'd': (0, 1), 'в': (0, 1),
}


class GameCharacter:
    def __init__(self, character_name: str, health_points: int, attack_power: int, team_side: str):
        self.character_name = character_name
        self.maximum_health = health_points
        self.current_health = health_points
        self.attack_power = attack_power
        self.team_side = team_side
        self.position_row = 0
        self.position_col = 0
        self.is_defeated = False

    def get_status_description(self) -> str:
        return f"{self.character_name} (HP: {self.current_health}/{self.maximum_health}, Сила: {self.attack_power})"

    def receive_damage(self, damage_amount: int):
        self.current_health -= damage_amount
        if self.current_health <= 0:
            self.current_health = 0
            self.is_defeated = True

    def perform_attack(self, target_character: 'GameCharacter'):
        damage_dealt = random.randint(self.attack_power - 2, self.attack_power + 2)
        print(f"{self.character_name} атакує {target_character.character_name} на {damage_dealt} шкоди!")
        target_character.receive_damage(damage_dealt)

    def update_position(self, new_row: int, new_col: int):
        self.position_row = new_row
        self.position_col = new_col

    def __str__(self):
        return self.character_name[0]


class WarriorCharacter(GameCharacter):
    def __init__(self, team_side: str = "enemy"):
        super().__init__("Воїн", random.randint(100, 150), random.randint(10, 20), team_side)
        self.armor_rating = random.randint(5, 10)

    def receive_damage(self, damage_amount: int):
        damage_after_armor = max(0, damage_amount - self.armor_rating)
        super().receive_damage(damage_after_armor)

    def __str__(self):
        return "В" if self.team_side == "enemy" else "Г"


class MageCharacter(GameCharacter):
    def __init__(self, team_side: str = "enemy"):
        super().__init__("Маг", random.randint(60, 90), random.randint(25, 40), team_side)
        self.mana_points = random.randint(50, 100)

    def __str__(self):
        return "М"


class ArcherCharacter(GameCharacter):
    def __init__(self, team_side: str = "enemy"):
        super().__init__("Лучник", random.randint(80, 110), random.randint(15, 25), team_side)
        self.accuracy_percent = random.randint(80, 100)

    def perform_attack(self, target_character: 'GameCharacter'):
        hit_chance = random.randint(1, 100)
        if hit_chance <= self.accuracy_percent:
            super().perform_attack(target_character)
        else:
            print(f"{self.character_name} промахнувся!")

    def __str__(self):
        return "Л"


class HealingPotion:
    def __init__(self):
        self.restoration_amount = random.randint(30, 50)
        self.position_row = 0
        self.position_col = 0

    def __str__(self):
        return "+"


class DungeonGame:
    def __init__(self, board_rows: int, board_cols: int):
        self.board_rows = board_rows
        self.board_cols = board_cols
        self.game_board = [[None for _ in range(board_cols)] for _ in range(board_rows)]
        self.player_hero = None
        self.enemy_list = []
        self.current_turn = 1
        self.event_log = []

    def add_to_event_log(self, event_message: str):
        self.event_log.append(event_message)
        if len(self.event_log) > 5:
            self.event_log.pop(0)

    def place_character_on_board(self, character: GameCharacter, row: int, col: int):
        is_valid_position = 0 <= row < self.board_rows and 0 <= col < self.board_cols
        is_cell_empty = self.game_board[row][col] is None if is_valid_position else False

        if is_valid_position and is_cell_empty:
            self.game_board[row][col] = character
            character.update_position(row, col)
            if character.team_side == "hero":
                self.player_hero = character
            else:
                self.enemy_list.append(character)
            return True
        return False

    def place_potion_on_board(self, row: int, col: int):
        is_valid_position = 0 <= row < self.board_rows and 0 <= col < self.board_cols
        is_cell_empty = self.game_board[row][col] is None if is_valid_position else False

        if is_valid_position and is_cell_empty:
            new_potion = HealingPotion()
            new_potion.position_row = row
            new_potion.position_col = col
            self.game_board[row][col] = new_potion
            return True
        return False

    def initialize_game_level(self):
        hero_character = WarriorCharacter(team_side="hero")
        hero_character.character_name = "Герой"
        hero_character.current_health = 200
        hero_character.maximum_health = 200
        hero_character.attack_power = 25
        hero_character.armor_rating = 15
        self.place_character_on_board(hero_character, 0, 0)

        available_enemy_types = [WarriorCharacter, MageCharacter, ArcherCharacter]
        total_enemies = 4

        for _ in range(total_enemies):
            while True:
                random_row = random.randint(2, self.board_rows - 1)
                random_col = random.randint(2, self.board_cols - 1)
                selected_enemy_type = random.choice(available_enemy_types)
                if self.place_character_on_board(selected_enemy_type(team_side="enemy"), random_row, random_col):
                    break

        for _ in range(2):
            while True:
                random_row = random.randint(0, self.board_rows - 1)
                random_col = random.randint(0, self.board_cols - 1)
                if self.place_potion_on_board(random_row, random_col):
                    break

    def try_move_or_attack(self, character: GameCharacter, direction_row: int, direction_col: int):
        target_row = character.position_row + direction_row
        target_col = character.position_col + direction_col

        is_within_bounds = 0 <= target_row < self.board_rows and 0 <= target_col < self.board_cols
        if not is_within_bounds:
            return

        cell_content = self.game_board[target_row][target_col]

        if isinstance(cell_content, HealingPotion) and character.team_side == "hero":
            heal_value = cell_content.restoration_amount
            character.current_health = min(character.maximum_health, character.current_health + heal_value)
            self.add_to_event_log(f"Герой підібрав зілля! +{heal_value} HP")
            self.game_board[target_row][target_col] = None
            self.game_board[character.position_row][character.position_col] = None
            self.game_board[target_row][target_col] = character
            character.update_position(target_row, target_col)
            return

        if cell_content and isinstance(cell_content, GameCharacter):
            target_is_enemy = cell_content.team_side != character.team_side
            if target_is_enemy:
                damage_dealt = random.randint(character.attack_power - 2, character.attack_power + 2)
                self.add_to_event_log(f"{character.character_name} атакує {cell_content.character_name} на {damage_dealt} шкоди!")

                if isinstance(cell_content, WarriorCharacter):
                    blocked_damage = min(damage_dealt, cell_content.armor_rating)
                    damage_after_block = max(0, damage_dealt - cell_content.armor_rating)
                    if blocked_damage > 0:
                        self.add_to_event_log(f"  Заблоковано {blocked_damage} шкоди.")
                    damage_dealt = damage_after_block

                cell_content.current_health -= damage_dealt
                if cell_content.current_health <= 0:
                    cell_content.current_health = 0
                    cell_content.is_defeated = True
                    self.add_to_event_log(f"{cell_content.character_name} переможений!")

                    self.game_board[target_row][target_col] = None
                    if cell_content in self.enemy_list:
                        self.enemy_list.remove(cell_content)
                    elif cell_content == self.player_hero:
                        self.player_hero = None
            else:
                if character.team_side == "hero":
                    self.add_to_event_log("Там союзник.")
        elif cell_content is None:
            self.game_board[character.position_row][character.position_col] = None
            self.game_board[target_row][target_col] = character
            character.update_position(target_row, target_col)

    def display_game_board(self):
        print(f"\n--- Хід {self.current_turn} ---")
        if self.player_hero:
            print(f"Герой HP: {self.player_hero.current_health}/{self.player_hero.maximum_health}")

        horizontal_separator = "-" * (self.board_cols * 4 + 1)
        print(horizontal_separator)
        for board_row in self.game_board:
            row_display = "|"
            for cell in board_row:
                cell_symbol = str(cell) if cell else " "
                row_display += f" {cell_symbol} |"
            print(row_display)
            print(horizontal_separator)

        print("\nЛегенда: Г=Герой В=Воїн М=Маг Л=Лучник +=Зілля")
        print("\n[Події]")
        for event_message in self.event_log:
            print(f"- {event_message}")

    def process_enemy_actions(self):
        for enemy_index, enemy_character in enumerate(self.enemy_list):
            if enemy_character.is_defeated or not self.player_hero:
                continue

            should_skip_turn = enemy_index % 2 == 1 and self.current_turn % 2 == 0
            if should_skip_turn:
                continue

            move_direction_row, move_direction_col = 0, 0
            if enemy_character.position_row < self.player_hero.position_row:
                move_direction_row = 1
            elif enemy_character.position_row > self.player_hero.position_row:
                move_direction_row = -1
            elif enemy_character.position_col < self.player_hero.position_col:
                move_direction_col = 1
            elif enemy_character.position_col > self.player_hero.position_col:
                move_direction_col = -1

            distance_to_hero = abs(enemy_character.position_row - self.player_hero.position_row) + \
                              abs(enemy_character.position_col - self.player_hero.position_col)

            if distance_to_hero == 1:
                damage_dealt = random.randint(enemy_character.attack_power - 2, enemy_character.attack_power + 2)
                self.add_to_event_log(f"{enemy_character.character_name} атакує Героя на {damage_dealt} шкоди!")

                if isinstance(self.player_hero, WarriorCharacter):
                    blocked_damage = min(damage_dealt, self.player_hero.armor_rating)
                    damage_after_block = max(0, damage_dealt - self.player_hero.armor_rating)
                    if blocked_damage > 0:
                        self.add_to_event_log(f"  Герой заблокував {blocked_damage} шкоди.")
                    damage_dealt = damage_after_block

                self.player_hero.current_health -= damage_dealt
                if self.player_hero.current_health <= 0:
                    self.player_hero.current_health = 0
                    self.player_hero.is_defeated = True
                    self.add_to_event_log("Герой переможений!")
            else:
                row_distance = abs(enemy_character.position_row - self.player_hero.position_row)
                col_distance = abs(enemy_character.position_col - self.player_hero.position_col)
                if row_distance > col_distance:
                    self.try_move_or_attack(enemy_character, move_direction_row, 0)
                else:
                    self.try_move_or_attack(enemy_character, 0, move_direction_col)

    def run_game_loop(self):
        self.initialize_game_level()
        print("Використовуйте WASD або ЦФІВ для руху. Q або Й для виходу.")
        print("Легенда: Г=Герой В=Воїн М=Маг Л=Лучник +=Зілля")
        input("Натисніть Enter для початку...")

        game_is_running = True
        while game_is_running:
            hero_is_alive = self.player_hero and not self.player_hero.is_defeated
            enemies_remain = len(self.enemy_list) > 0

            if not hero_is_alive or not enemies_remain:
                break

            os.system('clear')
            self.display_game_board()

            print("\nРух (WASD) або Вихід (Q)")
            pressed_key = read_single_keypress().lower()

            if pressed_key in ['q', 'й']:
                game_is_running = False
                break

            if pressed_key in MOVEMENT_KEYS:
                direction_row, direction_col = MOVEMENT_KEYS[pressed_key]
                self.try_move_or_attack(self.player_hero, direction_row, direction_col)
            else:
                continue

            hero_still_alive = self.player_hero and not self.player_hero.is_defeated
            enemies_still_exist = len(self.enemy_list) > 0
            if enemies_still_exist and hero_still_alive:
                self.process_enemy_actions()
                self.current_turn += 1

        os.system('clear')
        self.display_game_board()

        hero_lost = not self.player_hero or self.player_hero.is_defeated
        all_enemies_defeated = len(self.enemy_list) == 0

        if hero_lost:
            print("\nКІНЕЦЬ ГРИ! Ви програли.")
        elif all_enemies_defeated:
            print("\nПЕРЕМОГА! Всіх ворогів знищено.")
        else:
            print("\nГру зупинено.")


def start_game():
    dungeon_game = DungeonGame(6, 6)
    dungeon_game.run_game_loop()


if __name__ == "__main__":
    start_game()
