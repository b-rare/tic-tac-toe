"""Provides definitions to all states on a Tic-Tac-Toe cell.

Defines all known states of a Tic-Tac-Toe cell and methods to verify and get
the known states.
"""

__author__ = 'bwreher@gmail.com (Brandon Reher)'


class State(object):
  """Utility class representing all possible states of a Tic-Tac-Toe cell.

  Provides all known states of a Tic-Tac-Toe cell. Also contains static
  utility methods to get and verify states.

  Attributes:
    EMPTY: Cell has not been taken by either player.
    TAKEN_O: Cell has been taken by the 'O' player.
    TAKEN_X: Cell has been taken by the 'X' player.
  """
  EMPTY = 'empty'
  TAKEN_O = 'taken-o'
  TAKEN_X = 'taken-x'

  def __getitem__(self, key):
    """Defined to allow the State object to be accessed as a list.

    <em>This should not be used for anything critical!</em> This is only used
    to choose a player's token based on a random integer (list key).

    Returns:
      0: 'empty', '1': 'taken-o', '2': 'taken-x'. This is completely arbitrary
        and should not be relied on.
    """
    if isinstance(key, int):
      if key is 0:
        return self.EMPTY
      elif key is 1:
        return self.TAKEN_O
      elif key is 2:
        return self.TAKEN_X
      else:
        raise IndexError('Index %d is out of bounds.', key)

  @staticmethod
  def next_player(current_player):
    """Return the player whose turn it is after the current player.

    Implements a basic back-and-forth turn system for the Tic-Tac-Toe game.
    Note that this method provides no validation for the current player's token.

    Args:
      current_player: The token of the player whose turn it currently is.

    Returns:
      The next player to play in the turn system. Since no validation occurs
      in this method, State.TAKEN_X will be returned if the current_player is
      not a valid state.
    """
    return State.TAKEN_O if current_player is State.TAKEN_X else State.TAKEN_X

  @staticmethod
  def is_def(unverified_state):
    """Return the verification of the given state.

    Takes an unverified state object and checks for a match to any known state.

    Args:
      unverified_state: Any string that may be a possibly known state.

    Returns:
      True iff the given state is defined in the State object.
    """
    if unverified_state == State.TAKEN_X or unverified_state == State.TAKEN_O:
      return True
    
    return False
