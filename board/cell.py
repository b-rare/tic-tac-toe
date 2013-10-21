"""Basic representation of a Tic-Tac-Toe square.

Container of the square's coordinate position on the board and the
current state of the cell (empty or taken by a player). Provides a method to
'take' a cell for a given player.
"""

__author__ = 'bwreher@gmail.com (Brandon Reher)'

import logging

from state import State


class Error(Exception):
  """Base Error object."""


class IllegalStateChangeException(Error):
  """Exception for a bad state change in a cell."""


class Cell(object):
  """Basic definition of a Tic-Tac-Toe square.

  Provides basic access to each square's location and state in the grid.
  Also provides methods to validate and apply changes the state of the cell
  when the square is taken.

  Attributes:
    pos_x: An integer of the horizontal position on the grid.
    pos_y: An integer of the vertical position on the grid.
    state: The current State of the cell, or empty if the cell has no owner.
  """

  def __init__(self, pos_x, pos_y):
    """Initializes the cell to the specified cooardinates with no owner."""
    self.pos_x = pos_x
    self.pos_y = pos_y
    self.state = State.EMPTY

  def take(self, state):
    """Changes the state of the cell to taken by either player.

    Allows the caller to change the state of this cell to any state defined
    in the board.state module (except for State.EMPTY). If the specified state
    is not defined in the baord.state module, or the state is State.EMPTY,
    this will raise an exception to be hadled by the caller.

    Args:
      state: Any state defined in the board.State module.

    Raises:
      IllegalStateChangeException: Raised if the caller tries to change the
        state on a taken cell, changes the state to empty, or if the state is
        not a known state.
    """
    logging.debug('Attempting to change state from %s to %s',
                  self.state, state)
    if self.state != State.EMPTY:
      raise IllegalStateChangeException('Cannot change state of taken cell.')
    elif state == State.EMPTY:
      raise IllegalStateChangeException('Cannot take with empty state')
    elif State.is_def(state):
      self.state = state
    else:
      raise IllegalStateChangeException('State %s is undefined' % state)
