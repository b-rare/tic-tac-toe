"""Singleton providers of  high-level access to the underlying cells.

The Grid object contains a predefinied number of cells representing squares
on the Tic-Tac-Toe board. The object also provides utility methods to
manipulate the cells' state and check for notable game conditions like
wins or ties.
"""

__author__ = 'bwreher@gmail.com (Brandon Reher)'

import cell
import logging

from state import State


class Error(Exception):
  """Base Error for exceptions."""


class InvalidPositionValueException(Error):
  """Exception thrown when an invalid cell location is specified."""


class Grid(object):
  """Representation of a Tic-Tac-Toe grid.

  Single container object for many Cell objects, representing a Tic-Tac-Toe grid.
  The Grid provides order and access to the underlying Cells along with utility
  methods for the Tic-Tac-Toe game in progress.

  Attributes:
    board: 2D-tuple representing the current state Tic-Tac-Toe board.
    MAX_HORIZONTAL_CELLS: The maximum number of cells in the board's rows.
    MAX_VERTICAL_CELLS: The maximum number of cells in the board's columns.
    POSITION_X: Static key for the coordinate pair's X-axis.
    POSITION_Y: Static key for the coordinate pair's Y-axis.
  """

  MAX_HORIZONTAL_CELLS = 3
  MAX_VERTICAL_CELLS = 3

  POSITION_X = u'position_x'
  POSITION_Y = u'position_y'

  def __init__(self):
    """Initializes an empty Tic-Tac-Toe board."""
    self.board = self.__make_board()

  def __make_board(self):
    """Creates a Tic-Tac-Toe board with the maximum number of empty cells."""
    row = []
    board = []
    
    for x in range(self.MAX_HORIZONTAL_CELLS):
      for y in range(self.MAX_VERTICAL_CELLS):
        row.append(cell.Cell(x, y))
      board.append(tuple(row)) # Convert to tuple for row immutablity.
      row = [] 
    return tuple(board) # Tuple for immutablity of the board.

  def __is_column_win(self, player, row):
    """Checks for a winning column for the specified player.

    Iterates over the board state list to find a win for the given player. A win
    is defined as the player owning the entire column--or in terms of the
    board state, a win is the player owning every item in any sublist.

    Args:
      player: The player to check for a winning condition.
      row: The row (X-axis coordinate) of the player's last move. 
        Row is necessary to get the column entries from the board boate list.

    Returns:
      True iff the specified player owns every cell in the column.
    """
    board_state = self.to_state_list()

    logging.debug('Checking for %s column win with row %s', player, row)

    # Columns are stored as the second dimension of the list.
    # So we have to supply a row to get the column.
    column_state = board_state[int(row)]

    return column_state.count(player) == self.MAX_VERTICAL_CELLS

  def __is_row_win(self, player, column):
    """Checks for a winning row for the specified player.

    Iterates over the board state list to find a win for the given player. A win
    is defined as the player owning the entire row--or in terms of the
    board state, a win is the player owning every Nth position in all sublists.

    Args:
      player: The player to check for a winning condition.
      column: The column (Y-axis coordinate) of the player's last move. 
        Column is necessary to check that the Nth item is owned in each
        board state sublist.

    Returns:
      True iff the specified player owns every cell in a row.
    """
    board_state = self.to_state_list()
    row_state = []

    logging.debug('Checking for %s row win with column %s', player, column)
    
    # Since the state list is a 2D list, we must ensure
    # column consistency while checking the row.
    for x in range(self.MAX_HORIZONTAL_CELLS):
      row_state.append(board_state[x][int(column)])

    logging.debug('Row list: %s', row_state)
    return row_state.count(player) == self.MAX_HORIZONTAL_CELLS

  def __is_diagonal_win(self, player, column, row):
    """Checks for a winning diagonal for the given player.

    Diagonal wins are more directional than row or column wins, so wins are
    defined with a specific series of preconditions. If the preconditions are
    met, we have a winner. The current diagonal win algorithm breaks in game
    boards larger than 3x3.

    Args:
      player: The player to check for a winning condition.
      column: The column (Y-axis coordinate) of the player's last move. 
      row: The row (X-axis coordinate) of the player's last move.

    Returns:
      True iff the specified player owns every cell in a diagonal pattern.
    """
    middle_row = self.MAX_VERTICAL_CELLS/2
    middle_column = self.MAX_HORIZONTAL_CELLS/2

    logging.debug('Checking for %s diagonal win', player)

    # Check the middle as a necessary precondition.
    middle_owner = self.board[middle_column][middle_row].state
    logging.debug('Middle owned by %s', middle_owner)
    if middle_owner != player:
      return False

    # If the middle was taken, see if the player owns any left-side corners.
    if column == middle_column and row == middle_row:
      if self.board[0][0].state == player:
        row = 0
        column = 0
      elif self.board[0][self.MAX_VERTICAL_CELLS - 1].state == player:
        row = 0
        column = self.MAX_VERTICAL_CELLS - 1
      else:
        logging.debug('%s does not own a necessary corner', player)
        return False

    logging.debug('Row: %s, Column: %s', row, column)

    # Check the opposite corner of the cell that was taken.
    # (Subtract one due to 0-index lists.)
    opposite_column = column ^ (self.MAX_VERTICAL_CELLS - 1)
    opposite_row = row ^ (self.MAX_HORIZONTAL_CELLS - 1)

    logging.debug('Computed opposite row: %s column: %s', row, column)

    if (opposite_row < self.MAX_HORIZONTAL_CELLS and
        opposite_column < self.MAX_VERTICAL_CELLS):
        return self.board[opposite_row][opposite_column].state == player

    logging.debug('%s does not own an opposite corner', player)
    return False

  def check_coordinates(self, coordinate_pair):
    """Check that the requested coordinates are present on this board."""
    position_x = int(coordinate_pair.get(self.POSITION_X))
    position_y = int(coordinate_pair.get(self.POSITION_Y))

    if (position_x >= self.MAX_HORIZONTAL_CELLS or
        position_x < 0 or
        position_y >= self.MAX_VERTICAL_CELLS or
        position_y < 0):
      raise InvalidPositionValueException('Cell cannot be taken at position '
                                          '(%s, %s)' % (position_x, position_y))

  def contains_winner(self, current_player, last_move_coordinates):
    """Uses the coordinates of the last move to determine a game winner.

    Checks if the winner owns an entire row, column, or any diagonal.
    The checks use the positioning of the last taken cell for analyzing
    winning conditions in the last move's vicinity.

    Args:
      current_player: The player to check for a winning state.
      last_move_coordinates: Dict containing the X and Y-axis coordinates of
        the last taken cell.

    Returns:
      True iff the player has a winning condition on the board.
    """
    row = last_move_coordinates.get(self.POSITION_X)
    column = last_move_coordinates.get(self.POSITION_Y)

    return (self.__is_column_win(current_player, row) or
            self.__is_row_win(current_player, column) or
            self.__is_diagonal_win(current_player, column, row))

  def contains_tie(self):
    """Checks the board for a draw/tie.
    
    The board is likely in a draw/tie state if every cell is taken. Note that
    this method will not check for winning conditions. It's plausible that
    every cell is taken, but a player has a winning position.

    Returns:
      True iff every cell on the board is taken. Note that this does not
      indicate the absence of a win for a player.
    """
    for column_cell in range(self.MAX_HORIZONTAL_CELLS):
      for row_cell in range(self.MAX_VERTICAL_CELLS):
        if State.EMPTY == self.board[row_cell][column_cell].state:
          logging.debug('No draw/tie found.')
          return False

    logging.debug('Game is in a draw/tie state.')
    return True

  def to_state_list(self):
    """Creates a 2D list representing the current board's state.
    
    Useful when sending the board's current state as a JSON object. Accessors
    of the list should treat the board as an inverted coordinate plane with
    (0,0) being the top-left cell and (2,2) being the bottom-right cell.

    Returns:
      2D list of containing each cell's state.
    """
    column_list = []
    state_list = []
    for i in range(self.MAX_HORIZONTAL_CELLS):
      for j in range(self.MAX_VERTICAL_CELLS):
        column_list.append(self.board[i][j].state)
      state_list.append(column_list)
      column_list = []

    return state_list
