"""Unit tests for board.State class.

These tests will be flaky/volatile to changes in the base class.
"""

__author__ = 'bwreher@gmail.com (Brandon Reher)'

import unittest

from state import State


class StateTest(unittest.TestCase):
  """Unit tests for the board.State class."""

  def testNextPlayer(self):
    self.assertEqual(State.next_player(State.TAKEN_X), State.TAKEN_O)
    self.assertEqual(State.next_player(State.TAKEN_O), State.TAKEN_X)
    self.assertEqual(State.next_player('foo_player'), State.TAKEN_X)

  def testIsDefWithValidStates(self):
   self.assertTrue(State.is_def(State.TAKEN_X))
   self.assertTrue(State.is_def(State.TAKEN_O))
   self.assertFalse(State.is_def('foo_player'))


if __name__ == '__main__':
  unittest.main()
