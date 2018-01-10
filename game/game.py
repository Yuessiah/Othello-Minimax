import os
from collections import deque
from game.board import Board
from game.controllers import PlayerController, AiController
from game.random_controller import RandomController
from game.settings import *

__author__ = 'bengt, yuessiah'


class Game(object):
    """Game ties everything together. It has a board,
    two controllers, and can draw to the screen."""

    def __init__(self, timeout=1,
                 players=['ai', 'ai'],
                 colour=False):

        self.board = Board(colour)
        self.timeout = timeout
        self.ai_counter = 0
        self.list_of_colours = [BLACK, WHITE]
        self.ctrlers = deque([self.mk_ctrler(BLACK, players[0]), self.mk_ctrler(WHITE, players[1])])
        self.player = self.ctrlers[0].get_colour()
        self.board.set_black(4, 3)
        self.board.set_black(3, 4)
        self.board.set_white(4, 4)
        self.board.set_white(3, 3)
        self.board.mark_moves(self.player)
        self.previous_move = None


    def mk_ctrler(self, colour, ctrler_type):
        """ Returns a controller with the specified colour.
            'player' == PlayerController,
            'ai' == AiController.
        """
        if ctrler_type == 'player':
            return PlayerController(colour)
        elif ctrler_type == 'random':
            return RandomController(colour)
        else:
            self.ai_counter += 1
            return AiController(self.ai_counter, colour, self.timeout)


    def show_info(self):
        """ Prints game information to stdout.
        """
        self.player = self.ctrlers[0].get_colour()
        print("Playing as:       " + self.player)
        print("Current turn:     " + str(self.ctrlers[0]))
        print("Number of Black:  " + str(
            len([p for p in self.board.pieces if p.get_state() == BLACK])))
        print("Number of White:  " + str(
            len([p for p in self.board.pieces if p.get_state() == WHITE])))


    def show_board(self):
        """ Prints the current state of the board to stdout.
        """
        self.board.mark_moves(self.player)
        print(self.board.draw())


    def show_commands(self):
        """ Prints the possible moves to stdout.
        """
        moves = [self.coordinate(piece.get_position()) for piece in self.board.get_move_pieces(self.player)]

        if not moves:
            raise NoMovesError

        print("Possible moves are: ", moves)
        self.board.clear_moves()


    def run(self):
        """ The game loop will print game information, the board, the possible moves, and then wait for the
            current player to make its decision before it processes it and then goes on repeating itself.
        """
        while True:
            os.system('clear')
            self.show_info()
            self.show_board()

            try:
                self.show_commands()
                next_move = self.ctrlers[0].next_move(self.board)
                self.board.make_move(next_move, self.ctrlers[0].get_colour())
            except NoMovesError:
                print("Game Over")
                blacks = len([p for p in self.board.pieces if p.get_state() == BLACK])
                whites = len([p for p in self.board.pieces if p.get_state() == WHITE])

                if blacks > whites:
                    print("Black won this game.")
                    exit()
                elif blacks == whites:
                    print("This game was a tie.")
                    exit()
                else:
                    print("White won this game.")
                    exit()

            self.ctrlers.rotate()
            self.previous_move = next_move


    def coordinate(self, coordinate):
        """ Transforms an (x, y) tuple into (a-h, 1-8) tuple.
        """
        x, y = coordinate
        return '{0}{1}'.format(chr(ord('a') + x), y + 1)
