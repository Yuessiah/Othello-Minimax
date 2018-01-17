import copy
import datetime
import sys

__author__ = 'bengt, yuessiah'

from game.settings import *


class AlphaBetaPruner(object):
    """Alpha-Beta Pruning algorithm."""

    def __init__(self, mutex, duration, pieces, first_player, second_player):
        self.mutex = mutex
        self.board = 0
        self.move = 1
        self.white = 2
        self.black = 3
        self.max_depth = 0
        self.duration = duration
        self.complexity = 0
        self.lifetime = None
        self.first_player, self.second_player = (self.white, self.black) \
            if first_player == WHITE else (self.black, self.white)
        self.state = self.make_state(pieces)


    def make_state(self, pieces):
        """ Returns a tuple in the form of "current_state", that is: (current_player, state).
        """
        results = {BOARD: self.board, MOVE: self.board, WHITE: self.white, BLACK: self.black}
        return self.first_player, [results[p.get_state()] for p in pieces]


    def alpha_beta_search(self):
        """ Returns a valid action for the AI.
        """
        self.lifetime = datetime.datetime.now() + datetime.timedelta(seconds=self.duration)

        num_of_piece = 64 - self.state[1].count(0)
        if num_of_piece <= 9:
            self.max_depth = 2
        elif num_of_piece <= 18:
            self.max_depth = 3
        elif num_of_piece <= 36:
            self.max_depth = 4
        else:
            self.max_depth = 5

        fn = lambda action: self.negamax(depth=0, state=self.next_state(self.state, action), alpha=-float('Inf'), beta=float('Inf'))
        actions = self.get_moves(self.state[0], self.state[1])
        moves = [(fn(action), action) for action in actions]

        if len(moves) == 0:
            raise NoMovesError

        return max(moves, key=lambda value: value[0])[1]


    def negamax(self, depth, state, alpha, beta):
        """ Calculates the best possible move for the player.
        """
        if self.cutoff_test(depth):
            eval = self.evaluation(state[1], self.first_player)
            sys.stdout.write("\x1b7\x1b[%d;%dfDepth: %d, Eval: %f\x1b8" % (12, 22, depth, eval))
            self.complexity += 1
            sys.stdout.write("\x1b7\x1b[%d;%dfComplexity: %d\x1b8" % (13, 22, self.complexity))
            return eval

        value = alpha

        actions = self.get_moves(state[0], state[1])
        for action in actions:
            value = max([value, -self.negamax(depth + 1, self.next_state(state, action), -beta, -value)])
            if value >= beta:
                return value

        return value


    def evaluation(self, state, player_to_check):
        """ Returns a positive value when the player wins.
            Returns zero when there is a draw.
            Returns a negative value when the opponent wins."""

        player = player_to_check
        opponent = self.opponent(player)

        player_pieces = len([p for p in state if p == player])
        opponent_pieces = len([p for p in state if p == opponent])
        count_eval = player_pieces - opponent_pieces

        move_eval = -1 * len(self.get_moves(opponent, state))

        corners_player = (state[0] == player) + \
                         (state[7] == player) + \
                         (state[56] == player) + \
                         (state[63] == player)
        corners_opponent = (state[0] == opponent) + \
                           (state[7] == opponent) + \
                           (state[56] == opponent) + \
                           (state[63] == opponent)
        corners_eval = corners_player - corners_opponent

        edges_player = len([x for x in state if state == player and (state % 8 == 0 or state % 8 == 8)]) / (
            WIDTH * HEIGHT)
        edges_opponent = len([x for x in state if state == opponent and (state % 8 == 0 or state % 8 == 8)]) / (
            WIDTH * HEIGHT)
        edges_eval = edges_player - edges_opponent

        eval = count_eval * 120 + corners_eval * 6800 + edges_eval * 3200 + move_eval * 35

        return eval


    def opponent(self, player):
        """ Returns the opponent of the specified player.
        """
        return self.second_player if player is self.first_player else self.first_player


    def next_state(self, current_state, action):
        """ Returns the next state in the form of a "current_state" tuple, (current_player, state).
        """
        placed = action[0] + (action[1] * WIDTH)
        player = copy.copy(current_state[0])
        state  = copy.copy(current_state[1])

        state[placed] = player
        for d in DIRECTIONS:
            if outside_board(placed, d):
                continue

            tile = placed + d
            while state[tile] != self.board:
                if state[tile] == player or outside_board(tile, d):
                    break
                else:
                    state[tile] = player
                    tile += d

        return self.opponent(player), state


    def get_moves(self, player, state):
        """ Returns a generator of (x,y) coordinates.
        """
        moves = [self.mark_move(player, self.opponent(player), tile, state, d)
                 for tile in range(WIDTH * HEIGHT)
                 for d in DIRECTIONS
                 if not outside_board(tile, d) and state[tile] == player]

        return [(x, y) for found, x, y, tile in moves if found]


    def mark_move(self, player, opponent, tile, pieces, direction):
        """ Returns True whether the current tile piece is a move for the current player,
            otherwise it returns False.
        """
        if not outside_board(tile, direction):
            tile += direction
        else:
            return False, int(tile % WIDTH), int(tile / HEIGHT), tile

        if pieces[tile] == opponent:
            while pieces[tile] == opponent:
                if outside_board(tile, direction):
                    break
                else:
                    tile += direction

            if pieces[tile] == self.board:
                return True, int(tile % WIDTH), int(tile / HEIGHT), tile

        return False, int(tile % WIDTH), int(tile / HEIGHT), tile


    def cutoff_test(self, depth):
        """ Returns True when the cutoff limit has been reached.
        """
        return depth >= self.max_depth or datetime.datetime.now() > self.lifetime
