import os
import random

ships = [3, 2, 2, 1, 1, 1, 1]
board_size = 6

# исключение - выход за границы доски
class BoardOutException(Exception):
    pass

# исключение - неверное размещение корабля
class ShipPlacementException(Exception):
    pass

# исключение - выстрел в недопустимую клетку
class IncorrectShot(Exception):
    pass

# исключение - неправильный формат ввода
class InvalidInputException(Exception):
    pass


class Dot:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Ship:
    def __init__(self, length, bow, direction):
        self.length = length
        self.bow = bow
        self.direction = direction
        self._lives = length
        self.all_dots = None

    @property
    def lives(self):
        return self._lives

    def hit(self):
        self._lives -= 1
        return self._lives == 0

    def dots(self):
        if self.all_dots is not None:
            return self.all_dots
        self.all_dots = []
        start_x, start_y = self.bow
        for i in range(self.length):
            if self.direction == 1:  # вертикальное
                new_x = start_x + i
                new_y = start_y
            else:  # горизонтальное
                new_x = start_x
                new_y = start_y + i
            if not (0 <= new_x < board_size and 0 <= new_y < board_size):
                raise ShipPlacementException('Корабль выходит за пределы поля')
            self.all_dots.append([new_x, new_y])
        return self.all_dots

class Board:
    def __init__(self, hid=True):
        self._matrix = [['0'] * board_size for j in range(board_size)]
        self._ships = []
        self.hid = hid
        self._living_ships = len(ships)

    @property
    def all_ships_sunk(self):
        return self._living_ships == 0

    def add_ship(self, ship):
        # добавляем корабль
        for x, y in ship.dots():
            if self._matrix[x][y] != '0':
                raise ShipPlacementException(f"Клетка [{x+1}, {y+1}] уже занята!")
        for x, y in ship.dots():
            self._matrix[x][y] = '■'
        self._ships.append(ship)
        self.contour(ship)

    def contour(self, ship, contour_letter='K'):
        # рисуем контур кораблей
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for coord in ship.dots():
            x1, y1 = coord
            for x2, y2 in directions:
                x3, y3 = x1 + x2, y1 + y2
                if not self.out(Dot(x3, y3)):
                    if self._matrix[x3][y3] != '■' and self._matrix[x3][y3] != 'X':
                        self._matrix[x3][y3] = contour_letter

    def display_hid(self):
        print('   ' + '   '.join(str(i+1) for i in range(board_size)))
        for i, row in enumerate(self._matrix):
            display_row = []
            for j, cell in enumerate(row):
                if self.hid:
                    # на поле соперника скрываем контур и корабли
                    if cell == '■' or cell == 'K':
                        display_row.append('0')
                    else:
                        display_row.append(cell)
                else:
                    # если это наше поле, то отображаем его полностью
                    display_row.append(cell)
            print(str(i+1) + ' |' + '| |'.join(display_row) + '|')

    def out(self, dot):
        # проверяем, находятся ли введенные точки в границах поля
        return not (0 <= dot.x < board_size and 0 <= dot.y < board_size)

    def find_ship(self, dot):
        # ищем по точкам нужный корабль
        for ship in self._ships:
            if [dot.x, dot.y] in ship.dots():
                return ship

    def shot(self, dot):
        # проверка, стреляли ли мы уже в эту клетку
        if self._matrix[dot.x][dot.y] == 'T' or self._matrix[dot.x][dot.y] == 'X':
            raise IncorrectShot("Вы уже стреляли в эту клетку!")
        if not self.out(dot):
            # если попадаем - отнимаем жизни и ставим в клетку Х
            if self._matrix[dot.x][dot.y] == '■':
                self._matrix[dot.x][dot.y] = 'X'
                ship = self.find_ship(dot)
                if ship.hit():
                    # если уничтожили корабль - вычитаем количество оставшихся кораблей и устанавливаем контур
                    self._living_ships -= 1
                    self.contour(ship, 'T')
                    return 'sunk'
                else:
                     return 'hit'
            else:
                # если промазали - ставим в клетку T
                self._matrix[dot.x][dot.y] = 'T'
                return 'miss'
        else:
            raise BoardOutException(f"Клетка {dot.x+1}, {dot.y+1} находится за пределами доски")

class Player:
    def __init__(self, my_board, enemy_board):
        self.my_board = my_board
        self.enemy_board = enemy_board

    def ask(self):
        pass

    def move(self):
        while True:
            try:
                target = self.ask()
                result = self.enemy_board.shot(Dot(*target))
                print('Выстрел', [target[0]+1, target[1]+1])
                self.enemy_board.display_hid()
                if result == 'sunk':
                    print('Корабль уничтожен!')
                    # Проверка победы после уничтожения корабля
                    if self.enemy_board.all_ships_sunk:
                        return 'win'
                    continue
                elif result == 'hit':
                    print("Попадание")
                    # При попадании ходим снова
                    continue
                else:
                    print("Мимо")
                break
            except Exception as e:
                if isinstance(self, User):
                    print(f'Ошибка: {e}, попробуйте еще раз')


class User(Player):
    def ask(self):
        while True:
            # получаем точки для выстрела и проверяем их
            try:
                coords = list(map(int, input("Введите через пробел 2 точки (от 1 до 6): ").split()))
            except ValueError:
                print('Ошибка: Вводить можно только цифры, попробуйте еще раз')
            else:
                try:
                    if len(coords) != 2:
                        raise InvalidInputException("Ввести можно только 2 числа")
                    if not (1 <= coords[0] <= board_size and 1 <= coords[1] <= board_size):
                        raise IncorrectShot(f"Координаты должны быть от 1 до {board_size}")
                    # Преобразуем введенные координаты (1-6) во внутренние (0-5)
                    return coords[0]-1, coords[1]-1
                except Exception as e:
                    print(f'Ошибка: {e}, попробуйте еще раз')


class AI(Player):
    def __init__(self, my_board, enemy_board):
        super().__init__(my_board, enemy_board)
        # сохраняем все точки, куда можно выстрелить
        self.available_shots = [[x, y] for x in range(board_size) for y in range(board_size)]
        # перемешиваем список, чтобы стрелять по случайным точкам
        random.shuffle(self.available_shots)

    def ask(self):
        if self.available_shots:
            # если список не пустой - стреляем в последние координаты и удаляем их из списка
            return self.available_shots.pop()
        # если список пустой - стреляем в случайную точку
        return random.randint(0, board_size - 1), random.randint(0, board_size - 1)

class Game:
    def __init__(self):
        self.my_board = Board(hid=False)
        self.enemy_board = Board(hid=True)
        self.user = User(self.my_board, self.enemy_board)
        self.ai = AI(self.enemy_board, self.my_board)

    def random_board(self):
        board = Board()
        attempts = 0
        for ship_length in ships:
            placed = False
            while not placed and attempts < 3000:
                attempts += 1
                try:
                    # выбираются случайные точки и случайное направление
                    x = random.randint(0, board_size - 1)
                    y = random.randint(0, board_size - 1)
                    direction = (random.choice([1, 2]))
                    ship = Ship(ship_length, (x, y), direction)
                    board.add_ship(ship)
                    placed = True
                except ShipPlacementException:
                    continue
            if not placed:
                # если не удается разместить корабли, то пересоздается доска
                return self.random_board()
        print("Доска соперника создана успешно!")
        return board

    def greet(self):
        print("Добро пожаловать! Удачной игры!\n"
              "'0' - пустые точки,\n'■' - ваш корабль,\n'K' - контур вашего корабля,\n'X' - подбитые корабли соперника,\n"
              "'T' - контур подбитых вражеских кораблей и точки, куда вы уже стреляли")

    def setup_my_board(self):
        print('Расставьте ваши корабли:')
        board = Board(hid=False)
        board.display_hid()
        count = 0
        for i in ships:
            # пользователь расставляет корабли
            while True:
                try:
                    count += 1
                    print(f'\nРазмещаем корабль размером {i}.')
                    x, y = self.user.ask()
                    if i > 1:
                        direction = int(input('Направление (1-вертикальное, 2-горизонтальное): '))
                        if direction not in (1, 2):
                            raise InvalidInputException("Направление может быть только 1 или 2")
                    else:
                        # если длина 1, то направление не имеет значения, поэтому принудительно устанавливаем вертикальное
                        direction = 1
                    ship = Ship(i, (x, y), direction)
                    board.add_ship(ship)
                    not_full_lines = 0
                    # проверка переполнения поля
                    for line in board._matrix:
                        if '0' in line:
                            not_full_lines += 1
                    # если поле переполнено и все корабли еще не размещены, то пересоздаем поле
                    if not_full_lines == 0 and count < len(ships):
                        print('\nДоска переполнена! Пересоздание доски\n')
                        return self.setup_my_board()
                    break
                except Exception as e:
                    print(f'Ошибка: {e}, попробуйте еще раз')
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Ваше поле:")
            board.display_hid()
        return board

    def loop(self):
        self.enemy_board = self.random_board()
        self.my_board = self.setup_my_board()
        self.user.enemy_board = self.enemy_board
        self.user.my_board = self.my_board
        self.ai.my_board = self.enemy_board
        self.ai.enemy_board = self.my_board
        print("Игра начинается")
        while True:
            # Ход пользователя
            print('-----------ВАШ ХОД-----------')
            print('Поле соперника:')
            self.enemy_board.display_hid()
            result = self.user.move()
            if self.enemy_board.all_ships_sunk:
                print("Поздравляем! Вы победили!")
                break
            print('--------ХОД СОПЕРНИКА--------')
            print('Ваше поле:')
            # Ход соперника
            result = self.ai.move()
            if self.my_board.all_ships_sunk:
                print("Вы проиграли!")
                break

    def start(self):
        self.greet()
        self.loop()

g = Game()
g.start()