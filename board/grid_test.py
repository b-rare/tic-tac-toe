"""Unit tests for the board.Grid class."""

__author__ = 'bwreher@gmail.com (Brandon Reher)'

import grid
import unittest

from state import State


class GridTest(unittest.TestCase):
  """Unit tests for the board.Grid class."""

  def setUp(self):
    self.game_board = grid.Grid()

  def testToStateListWithEmptyGridShouldBeEmpty(self):
    expected_board = []
    for i in range(3):
      expected_board.append([State.EMPTY, State.EMPTY, State.EMPTY])
      
    self.assertEqual(self.game_board.to_state_list(), expected_board)

  def testToStateListWithSomeTaken(self):
    self.game_board.board[0][0].take(State.TAKEN_X)
    self.game_board.board[1][0].take(State.TAKEN_O)
    self.game_board.board[1][2].take(State.TAKEN_X)

    in_progress_board = self.game_board.to_state_list()

    self.assertEqual(in_progress_board[0][0], State.TAKEN_X)
    self.assertEqual(in_progress_board[1][0], State.TAKEN_O)
    self.assertEqual(in_progress_board[1][2], State.TAKEN_X)

  def testContainsWinnerWithRowWin(self):
    self.game_board.board[0][1].take(State.TAKEN_X)
    self.game_board.board[2][1].take(State.TAKEN_X)
    self.game_board.board[1][1].take(State.TAKEN_X)

    self.assertTrue(self.game_board.contains_winner(State.TAKEN_X,
                                                    {'position_x': 1,
                                                     'position_y': 1}))
      
  def testContainsWinnerWithColumnWin(self):
    self.game_board.board[2][2].take(State.TAKEN_O)
    self.game_board.board[2][1].take(State.TAKEN_O)
    self.game_board.board[2][0].take(State.TAKEN_O)

    self.assertTrue(self.game_board.contains_winner(State.TAKEN_O,
                                                    {'position_x': 2,
                                                     'position_y': 0}))

  def testContainsWinnerWithTopLeftDiagonalWin(self):
    self.game_board.board[1][1].take(State.TAKEN_X)
    self.game_board.board[2][2].take(State.TAKEN_X)
    self.game_board.board[0][0].take(State.TAKEN_X)

    self.assertTrue(self.game_board.contains_winner(State.TAKEN_X,
                                                    {'position_x': 0,
                                                     'position_y': 0}))

  def testContainsWinnerWithTopRightDiagonalWin(self):
    self.game_board.board[2][0].take(State.TAKEN_O)
    self.game_board.board[0][2].take(State.TAKEN_O)
    self.game_board.board[1][1].take(State.TAKEN_O)

    self.assertTrue(self.game_board.contains_winner(State.TAKEN_O,
                                                    {'position_x': 1,
                                                     'position_y': 1}))

  def testContainsWinnerWithNoWin(self):
    self.game_board.board[2][2].take(State.TAKEN_X)
    self.game_board.board[0][0].take(State.TAKEN_O)
    self.game_board.board[1][1].take(State.TAKEN_X)

    self.assertFalse(self.game_board.contains_winner(State.TAKEN_X,
                                                     {'position_x': 1,
                                                      'position_y': 1}))


  def testContainsTieWithNoTieAndNoWin(self):
    self.game_board.board[2][2].take(State.TAKEN_X)
    self.game_board.board[0][0].take(State.TAKEN_O)
    self.game_board.board[1][1].take(State.TAKEN_X)

    self.assertFalse(self.game_board.contains_tie())

  def testContainsTieWithTieAndNoWin(self):
    self.game_board.board[0][0].take(State.TAKEN_X)
    self.game_board.board[0][1].take(State.TAKEN_O)
    self.game_board.board[0][2].take(State.TAKEN_X)

    self.game_board.board[1][0].take(State.TAKEN_O)
    self.game_board.board[1][1].take(State.TAKEN_O)
    self.game_board.board[1][2].take(State.TAKEN_X)

    self.game_board.board[2][0].take(State.TAKEN_X)
    self.game_board.board[2][1].take(State.TAKEN_X)
    self.game_board.board[2][2].take(State.TAKEN_O)

    self.assertTrue(self.game_board.contains_tie())

  def testContainsTieWithTieAndWin(self):
    self.game_board.board[0][0].take(State.TAKEN_X)
    self.game_board.board[0][1].take(State.TAKEN_O)
    self.game_board.board[0][2].take(State.TAKEN_X)

    self.game_board.board[1][0].take(State.TAKEN_X)
    self.game_board.board[1][1].take(State.TAKEN_O)
    self.game_board.board[1][2].take(State.TAKEN_X)

    self.game_board.board[2][0].take(State.TAKEN_X)
    self.game_board.board[2][1].take(State.TAKEN_O)
    self.game_board.board[2][2].take(State.TAKEN_X)

    self.assertTrue(self.game_board.contains_tie())

  def testCheckCoordinatesWithInvalidCoordinates(self):
    self.assertRaises(grid.InvalidPositionValueException,
                      self.game_board.check_coordinates,
                      {'position_x': '-1', 'position_y': '-1'})

    self.assertRaises(grid.InvalidPositionValueException,
                      self.game_board.check_coordinates,
                      {'position_x': '999', 'position_y': '999'})

    self.assertRaises(grid.InvalidPositionValueException,
                      self.game_board.check_coordinates,
                      {'position_x': '-1', 'position_y': '2'})

    self.assertRaises(grid.InvalidPositionValueException,
                      self.game_board.check_coordinates,
                      {'position_x': '0', 'position_y': '-2'})


if __name__ == '__main__':
  unittest.main()
