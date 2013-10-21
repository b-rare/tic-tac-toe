"""Web Handler for the GAE Tic-Tac-Toe game.

Provides a basic Tic-Tac-Toe template on the first GET request.  Then allows 
RPCs to be handled via POST requests to manipulate the game's board throughout
the course of the game. Shares data using webapp2.application implementation
and provides no session support.
"""

__author__ = 'bwreher@gmail.com (Brandon Reher)'

import jinja2
import json
import logging
import os
import random
import webapp2

from board import grid
from board.cell import IllegalStateChangeException
from board.state import State

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__) + '/templates/'),
  extensions=['jinja2.ext.autoescape'])


class Play(webapp2.RequestHandler):
  """Base responder for the default GET request on the application."""

  def get(self):
    """Set game defaults, save them in a shared registry, then respond."""
    app = webapp2.get_app()

    app.registry['grid'] = grid.Grid()
    app.registry['player'] = State()[random.randint(1, 2)]
    app.registry['current_turn'] = State.TAKEN_X

    template_values = {'board': app.registry.get('grid').board,
                       'current_turn': State.TAKEN_X,
                       'player': app.registry.get('player')}

    template = JINJA_ENVIRONMENT.get_template('play.html')
    self.response.write(template.render(template_values))

  def post(self):
    """Not implemented."""
    self.error(403)

class RpcHandler(webapp2.RequestHandler):
  """API handler for incoming RPC requests.

  Responds to API requests via the POST method for a single game of Tic-Tac-Toe.
  The RpcHandler keeps track of the current game's state and provides
  methods to modify the game in response to requested actions.

  Attributes:
    COMPUTER: Key for the computer's token.
    CURRENT_TURN: Key for the current turn's token.
    FAILED: Key for a failed action status.
    GRID: Key for the game's grid.
    IN_PROGRESS: Key for the game's in progress status.
    MESSAGE: Key for messages that appear in the butterbar.
    PLAYER: Key for the human player's token.
    TIE: Key for the draw/tie game status.
    TOKENS: Key holding the current turn and human player tokens.
    STATUS: Key for the game's status (win, draw, lose, etc).
    WIN: Key for the winning game status.
  """

  COMPUTER = u'computer'
  CURRENT_TURN = u'current_turn'
  FAILED = u'failed'
  GRID = u'grid'
  IN_PROGRESS = u'in_progress'
  MESSAGE = u'message'
  PLAYER = u'player'
  STATUS = u'status'
  TIE = u'tie'
  TOKENS = u'tokens'
  WIN = u'win'

  def get(self):
    """Not implemented."""
    self.error(403)

  def post(self):
    """Request handler for POST requests."""
    logging.debug(self.request)

    # Get saved application state.
    app = webapp2.get_app()

    # Application can occasionally lose state.
    if app.registry.get('grid') is None:
      logging.warn('No board found in application.')
      logging.debug(webapp2.get_app())

      response = {self.STATUS: self.FAILED,
                  self.MESSAGE: 'Board not ready. Please refresh the page.'}
      logging.debug(response)
      self.response.write(json.dumps(response))
      return

    request = json.loads(self.request.body)

    action = request.get('action')
    player = request.get('player')
    logging.info('Action: %s Player: %s', action, player)

    if action == 'reset':
      logging.info('Reset board by player %s.', player)
      response = self.__reset_board(app)
    elif action == 'take':
      position_x = request.get('x')
      position_y = request.get('y')

      logging.info('Trying to take (%s, %s) as %s',
                   position_x,
                   position_y,
                   player)

      response = self.__take_cell(app,
                                  player,
                                  position_x,
                                  position_y)
    else:
      logging.warn('Unknown action: %s', action)
      response = {self.STATUS: self.FAILED,
                  self.MESSAGE: 'Cannot recognize action: %s' % action}

    logging.debug(response)
    self.response.write(json.dumps(response))

  def __reset_board(self, app):
    """Reset the board back to the default state.
    
    Resets the game's grid to an empty state, randomly chooses a new token for
    the human player, and resets the first move back to the 'X' token.

    Args:
      app: The webapp2 Application object.

    Returns:
      A dict mapping the game's grid, state, and players to their default
      values. This is later sent to the requester as a JSON object.
    """

    app.registry['grid'] = grid.Grid()
    app.registry['player'] = State()[random.randint(1, 2)]
    app.registry['current_turn'] = State.TAKEN_X

    computer = State.next_player(app.registry.get('player'))

    logging.info('Sucessfully reset the game.')
    logging.debug('Player is now %s', app.registry.get('player'))

    return {self.GRID: app.registry.get('grid').to_state_list(),
            self.STATUS: self.IN_PROGRESS,
            self.TOKENS: {self.COMPUTER: computer,
                          self.CURRENT_TURN: State.TAKEN_X,
                          self.PLAYER: app.registry.get('player')}}

  def __take_cell(self, app, player, position_x, position_y):
    """Takes the cell at the given coordinates on behalf of the player.
    
    Validates the request's coordinates and player's turn based on the internal
    game state. Takes the cell iff the coordinates exist on the game board,
    are not already taken by any player, and it is the specified player's turn.
    Otherwise, returns an error to be displayed in the butterbar.

    Args:
      app: The webapp2 Application object.
      player: Player token of the requester.
      position_x: The X-axis position of the cell to take.
      position_y: The Y-axis position of the cell to take.

    Returns:
      A dict containing the game's status with either the updated grid and 
      player tokens on success or error message on failure. This dict will
      later be converted to JSON and sent to the requester.
    """

    game_grid = app.registry.get('grid')
    current_player = app.registry.get('current_turn')

    logging.debug(game_grid)
    logging.debug('Current player: %s', current_player)

    if player != current_player:
      logging.warn('Player %s is not the current player (%s)',
                   player,
                   current_player)
      return {self.STATUS: self.FAILED, self.MESSAGE: 'Wait your turn'}

    try:
      logging.info('Checking coordinates (%s, %s)',
                   position_x, position_y)

      # Check the validity of the given coordinate values.
      game_grid.check_coordinates({game_grid.POSITION_X: position_x,
                                   game_grid.POSITION_Y: position_y})
    except grid.InvalidPositionValueException as e:
      logging.error('Invalid coordinates: %s', str(e))
      return {self.STATUS: self.FAILED, self.MESSAGE: str(e)}

    logging.debug('Coordinates (%s, %s) passed checks',
                  position_x,
                  position_y)

    try:
      logging.info('Take operation on (%s, %s) as %s',
                   position_x,
                   position_y,
                   player)

      # Actually attempt to take the cell.
      game_grid.board[position_x][position_y].take(player)
    except IllegalStateChangeException as e:
      logging.error('Unable to take cell: %s', str(e))
      return {self.STATUS: self.FAILED, self.MESSAGE: str(e)}

    logging.info('Sucessfully took (%s, %s) as %s',
                 position_x,
                 position_y,
                 player)

    logging.debug('Checking for draw or win on board.')
    # Check for notable game states (win or draw/tie).
    if game_grid.contains_winner(current_player,
                                 {game_grid.POSITION_X: position_x,
                                  game_grid.POSITION_Y: position_y}):
      logging.info('Player %s has won by taking (%s, %s)',
                   current_player,
                   position_x,
                   position_y)
      win_name = 'You' if current_player == app.registry.get('player') else 'I'
      return {self.GRID: game_grid.to_state_list(),
              self.MESSAGE: '%s won!' % win_name,
              self.STATUS: self.WIN, 
              self.TOKENS: {self.CURRENT_TURN: player, self.PLAYER: player}}
    elif game_grid.contains_tie():
      logging.info('Player %s has tied by taking (%s, %s)',
                   current_player,
                   position_x,
                   position_y)
      return {self.GRID: game_grid.to_state_list(),
              self.MESSAGE: 'Game is a draw',
              self.STATUS: self.TIE,
              self.TOKENS: {self.CURRENT_TURN: player, self.PLAYER: player}}
    
    app.registry['current_turn'] = State.next_player(current_player)
    computer = State.next_player(app.registry.get('player'))
    logging.debug('Current player is now %s', app.registry.get('current_turn'))

    return {self.GRID: game_grid.to_state_list(),
            self.STATUS: self.IN_PROGRESS, 
            self.TOKENS: {self.COMPUTER: computer,
                          self.CURRENT_TURN: app.registry.get('current_turn'),
                          self.PLAYER: app.registry.get('player')}}
            

# Set up class routing for URL parameters.
app = webapp2.WSGIApplication([
    ('/', Play),
    ('/rpc', RpcHandler),
    ], debug=False)
