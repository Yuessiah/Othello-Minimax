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
        sys.stdout.write("\x1b7\x1b[%d;%dfMax depth: %d\x1b8" % (10, 22, self.max_depth))

        fn = lambda next_action: self.opening_evaluation(next_action[1], self.first_player) + \
                self.negamax(0, next_action, -float('Inf'), float('Inf'))
        actions = self.get_moves(self.state[0], self.state[1])
        moves = [(fn(self.next_state(self.state, action)), action) for action in actions]

        if len(moves) == 0:
            raise NoMovesError

        return max(moves, key=lambda value: value[0])[1]


    def negamax(self, depth, state, alpha, beta):
        if self.cutoff_test(depth):
            eval = self.ending_evaluation(state[1], self.first_player)
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

    def opening_evaluation(self, state, player_to_check):
        board  = self.board
        player = player_to_check

        X = (state[0]  == board and state[9]  == player) or \
            (state[7]  == board and state[14] == player) or \
            (state[56] == board and state[49] == player) or \
            (state[63] == board and state[54] == player)

        C = (state[0]  == board and (state[1]  == player or state[8]  == player)) or \
            (state[7]  == board and (state[6]  == player or state[15] == player)) or \
            (state[56] == board and (state[48] == player or state[57] == player)) or \
            (state[63] == board and (state[55] == player or state[62] == player))

        if state.count(0) <= 16:
            eval = (X*-220) + (C*-115)
        else:
            eval = (X*-356) + (C*-215)
        sys.stdout.write("\x1b7\x1b[%d;%dfOpening eval: %d\x1b8" % (11, 22, eval))
        return eval


    def ending_evaluation(self, state, player_to_check):
        player   = player_to_check
        opponent = self.opponent(player)
        edge_eval = mobility = corner_eval = 0

        player_piece   = len([p for p in state if p == player  ])
        opponent_piece = len([p for p in state if p == opponent])
        count_eval = (player_piece - opponent_piece) / (player_piece + opponent_piece)

        player_move   = len(self.get_moves(player  , state))
        opponent_move = len(self.get_moves(opponent, state))
        if player_move + opponent_move:
            mobility = (player_move - opponent_move) / (player_move + opponent_move)

        corner_player   = (state[0]  == player  ) + (state[7]  == player  ) + \
                          (state[56] == player  ) + (state[63] == player  )
        corner_opponent = (state[0]  == opponent) + (state[7]  == opponent) + \
                          (state[56] == opponent) + (state[63] == opponent)
        if corner_player + corner_opponent:
            corner_eval = (corner_player - corner_opponent) / (corner_player + corner_opponent)

        edge_player   = len([p for i, p in enumerate(state) if p == player   and (i%8==0 or i%8==7 or i/8==0 or i/8==7)])
        edge_opponent = len([p for i, p in enumerate(state) if p == opponent and (i%8==0 or i%8==7 or i/8==0 or i/8==7)])
        if edge_player + edge_opponent:
            edge_eval = (edge_player - edge_opponent) / (edge_player + edge_opponent)

        if state.count(0) <= 8:
            eval = (count_eval*160) + (corner_eval*155) + (edge_eval*110) + (mobility*140)
        else:
            eval = (count_eval*100) + (corner_eval*185) + (edge_eval*155) + (mobility*165)
        sys.stdout.write("\x1b7\x1b[%d;%dfEnding eval: %f\x1b8" % (12, 22, eval))
        return eval


    def opponent(self, player):
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
                 for tile, colour in enumerate(state)
                 for d in DIRECTIONS
                 if colour == player and not outside_board(tile, d)]

        return list(set([(x, y) for found, x, y in moves if found]))


    def mark_move(self, player, opponent, tile, pieces, direction):
        """ Returns True whether the current tile piece is a move for the current player,
            otherwise it returns False.
        """
        tile += direction

        if pieces[tile] == opponent:
            while pieces[tile] == opponent and not outside_board(tile, direction):
                tile += direction

            if pieces[tile] == self.board:
                return True, int(tile%WIDTH), int(tile/HEIGHT)

        return False, int(tile%WIDTH), int(tile/HEIGHT)


    def cutoff_test(self, depth):
        return depth >= self.max_depth or datetime.datetime.now() > self.lifetime
