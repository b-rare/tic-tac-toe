"""Unit tests for the board.Cell class."""

__author__ = 'bwreher@gmail.com (Brandon Reher)'

import cell
import unittest

from state import State


class CellTest(unittest.TestCase):
  """Unit tests for the board.Cell class."""

  def setUp(self):
    self.empty_top_left = cell.Cell(0, 0)
    self.taken_x_middle = cell.Cell(1, 1)
    self.taken_x_middle.state = State.TAKEN_X

  def testTakeCellWithXPlayerShouldChangeState(self):
    self.assertEqual(self.empty_top_left.state, State.EMPTY)
    self.empty_top_left.take(State.TAKEN_X)
    self.assertEqual(self.empty_top_left.state, State.TAKEN_X)

  def testTakeAlreadyTakenCellShouldThrowException(self):
    self.assertRaises(cell.IllegalStateChangeException,
                      self.taken_x_middle.take,
                      'TAKEN_O')

  def testTakeCellWithInvalidStateShouldThrowException(self):
    self.assertRaises(cell.IllegalStateChangeException,
                      self.empty_top_left.take,
                      'TAKEN_Y')

  def testTakeCellWithEmptyStateShouldThrowException(self):
    self.assertRaises(cell.IllegalStateChangeException,
                      self.empty_top_left.take,
                      State.EMPTY)

if __name__ == '__main__':
  unittest.main()
