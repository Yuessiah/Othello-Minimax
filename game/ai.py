import copy
import datetime
import sys

__author__ = 'bengt, yuessiah'

from game.settings import *


class AlphaBetaPruner(object):
    """Alpha-Beta Pruning algorithm."""

    def __init__(self, mutex, duration, pieces, first_player, second_player):
        self.mutex = mutex
        self.board = 2
        self.white = 0
        self.black = 1
        self.max_depth = 0
        self.duration = duration
        self.complexity = 0
        self.lifetime = None
        self.first_player, self.second_player = (self.white, self.black) \
            if first_player == WHITE else (self.black, self.white)
        self.state = self.make_state(pieces)

    def make_state(self, pieces):
        results = {BOARD: self.board, MOVE: self.board, WHITE: self.white, BLACK: self.black}
        return [results[p.get_state()] for p in pieces], self.first_player

    def alpha_beta_search(self):
        self.lifetime = datetime.datetime.now() + datetime.timedelta(seconds=self.duration)

        left = self.state[0].count(self.board)
        if left >= 44:
            self.max_depth = 4
        else:
            self.max_depth = 5
        sys.stdout.write("\x1b7\x1b[%d;%dfMax depth: %d\x1b8" % (10, 22, self.max_depth))

        moves = self.get_moves(self.state[0], self.state[1])
        if len(moves) == 0:
            raise NoMovesError

        fn = lambda state, move: self.opening_evaluation(state[0], self.first_player, move) + \
                self.negamax(0, state, move, -float('Inf'), float('Inf'))
        scores = [(fn(self.next_state(self.state, move), move), move) for move in moves]

        return max(scores, key=lambda value: value[0])[1]

    def negamax(self, depth, state, action, alpha, beta):
        if self.cutoff_test(depth):
            eval = self.ending_evaluation(state[0], self.first_player^(depth&1), action)
            self.complexity += 1
            sys.stdout.write("\x1b7\x1b[%d;%dfComplexity: %d\x1b8" % (13, 22, self.complexity))
            sys.stdout.flush()
            return eval

        value = alpha
        moves = self.get_moves(state[0], state[1])
        for move in moves:
            value = max([value, -self.negamax(depth + 1, self.next_state(state, move), move, -beta, -value)])
            if value >= beta:
                return value

        return value

    def opening_evaluation(self, state, player, action):
        board  = self.board
        placed = action[0] + (action[1] * WIDTH)
        parity_count = [1]

        X = (state[0]  == board and state[9]  == player) + \
            (state[7]  == board and state[14] == player) + \
            (state[56] == board and state[49] == player) + \
            (state[63] == board and state[54] == player)

        C = (state[0]  == board and (placed == 1  or placed == 8 )) or \
            (state[7]  == board and (placed == 6  or placed == 15)) or \
            (state[56] == board and (placed == 48 or placed == 57)) or \
            (state[63] == board and (placed == 55 or placed == 62))

        parity = 1 if self.parity(0, copy.copy(state), placed, parity_count) else -0.75 #odd: 1, even: -0.75

        if state.count(board) <= 16:
            eval = (X*-320) + (C*-215)
        else:
            eval = (X*-456) + (C*-315)

        if parity_count[0] > 7:
            eval += parity * 110
        else:
            eval += parity * 365

        sys.stdout.write("\x1b7\x1b[%d;%dfOpening eval: %f\x1b8" % (11, 22, eval))
        return eval

    def ending_evaluation(self, state, player_to_check, action):
        board    = self.board
        player   = player_to_check
        opponent = self.opponent(player)
        edge_eval = mobility = corner_eval = stability_eval = 0

        player_piece   = len([p for p in state if p == player  ])
        opponent_piece = len([p for p in state if p == opponent])
        count_eval = (player_piece - opponent_piece) / (player_piece + opponent_piece)

        player_move   = len(self.get_moves(state, player))
        opponent_move = len(self.get_moves(self.next_state((state, player), action)[0], opponent))
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

        player_stability   = self.stability(state, player, opponent)
        opponent_stability = self.stability(self.next_state((state, player), action)[0], opponent, player)
        if player_stability + opponent_stability:
            stability_eval = (player_stability - opponent_stability) / (player_stability + opponent_stability)

        left = state.count(board)
        if left <= 18:
            eval = (count_eval*120) + (corner_eval*145) + (edge_eval*130) + (mobility*240) + (stability_eval*195)
        elif left <= 48:
            eval = (count_eval*100) + (corner_eval*185) + (edge_eval*100) + (mobility*165) + (stability_eval*185)
        else:
            eval = (count_eval*50)  + (corner_eval*115) + (edge_eval*150) + (mobility*115) + (stability_eval*285)

        if state.count(board) <= 7: #TODO: brute force
            eval += count_eval*370

        sys.stdout.write("\x1b7\x1b[%d;%dfEnding eval: %f\x1b8" % (12, 22, eval))
        return eval

    def opponent(self, player):
        return self.second_player if player is self.first_player else self.first_player

    def parity(self, depth, state, placed, count):
        for d in DIRECTIONS:
            if outside_board(placed, d):
                continue
            if state[placed+d] == self.board:
                count[0] += 1
                state[placed+d] = 1 #visited
                self.parity(depth + 1, state, placed+d, count)

        if depth == 0:
            return count[0] % 2

    def stability(self, state, player, opponent):
        bad_piece = set()

        for piece, colour in enumerate(state):
            if colour != opponent:
                continue

            for d in DIRECTIONS:
                if outside_board(piece, d):
                    continue

                to_store = set()
                tile = piece + d
                while state[tile] == player and not outside_board(tile, d):
                    to_store.add((int(tile%WIDTH), int(tile/HEIGHT)))
                    tile += d

                if state[tile] == self.board:
                    bad_piece.update(to_store)

        return state.count(player) - len(bad_piece)

    def next_state(self, current_state, action):
        placed   = action[0] + (action[1] * WIDTH)
        state    = copy.copy(current_state[0])
        player   = copy.copy(current_state[1])
        opponent = self.opponent(player)

        state[placed] = player
        for d in DIRECTIONS:
            if outside_board(placed, d):
                continue

            to_flip = []
            tile = placed + d
            while state[tile] == opponent and not outside_board(tile, d):
                to_flip.append(tile)
                tile += d

            if state[tile] == player:
                for piece in to_flip:
                    state[piece] = player

        return state, opponent

    def get_moves(self, state, player):
        """ Returns a generator of (x,y) coordinates.
        """
        moves = [self.mark_move(self.opponent(player), tile, state, d)
                 for tile, colour in enumerate(state)
                 for d in DIRECTIONS
                 if colour == player and not outside_board(tile, d)]

        return list(set([(x, y) for found, x, y in moves if found]))

    def mark_move(self, opponent, tile, pieces, direction):
        tile += direction

        while pieces[tile] == opponent and not outside_board(tile, direction):
            tile += direction
            if pieces[tile] == self.board:
                return True, int(tile%WIDTH), int(tile/HEIGHT)

        return False, int(tile%WIDTH), int(tile/HEIGHT)

    def cutoff_test(self, depth):
        return depth >= self.max_depth or datetime.datetime.now() > self.lifetime
