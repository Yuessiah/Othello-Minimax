#!/usr/bin/env python3

import argparse
from game.game import Game


def main():
    """ Reversi game with human player vs AI player.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', help="Number of seconds the brain is allowed to think before making its move",
                        type=int, default=1)
    parser.add_argument('--display-moves', help="Whether legal moves should be displayed or not", action='store_true')
    parser.add_argument('--text', help="Display the game in text mode", action='store_false')
    parser.add_argument('--player', help="Player first", action='store_true')
    parser.add_argument('--ai', help="AI first", action='store_true')
    parser.add_argument('--verify', help="Verify AI using a random player", action='store_true')

    args = parser.parse_args()

    if args.timeout < 0:
        exit()

    players=['player', 'player']
    if args.player:
        players = ['player', 'ai']
    if args.ai:
        players = ['ai', 'player']
    elif args.verify:
        players = ['ai', 'random']

    game = Game(timeout=args.timeout,
                display_moves=args.display_moves,
                colour=args.text,
                players=players)
    game.run()


if __name__ == "__main__":
    main()
