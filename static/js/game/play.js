/**
 * @fileoverview Tic-Tac-Toe game initializer and AI for the computer player.
 * @author bwreher@gmail.com (Brandon Reher)
 */

goog.provide('game.Play');

goog.require('game.TicTacToe');
goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.pubsub.PubSub');
goog.require('goog.string');


/**
 * Receives notifications about the game's state and determines the best
 * available move on the board. Once the best move has been determined,
 * requests that the cell is taken by the computer player.
 *
 * @param {string} baseApiUrl URL for the game's RPC server.
 * @param {string} topic PubSub topic to subscribe to for the computer's turn.
 * @constructor
 */
game.Play = function(baseApiUrl, topic) {
  /**
   * The computer's game token. Necessary for generating
   * a heuristic score for the game board.
   *
   * @private
   * @type {string}
   */
  this.me_ = null;

  /**
   * The human player's game token. Predominately needed for generating
   * a heuristic score for the game board.
   *
   * @private
   * @type {string}
   */
  this.opponent_ = null;

  /**
   * PubSub object to receive subscription events.
   *
   * @private
   * @type {goog.pubsub.PubSub}
   */
  this.pubSub_ = new goog.pubsub.PubSub();

  /**
   * Pubsub topic to subscribe.
   *
   * @private
   * @type {string}
   */
  this.topic_ = topic;

  /**
   * Utility class for Tic-Tac-Toe board manipulation. Order is important,
   * this has to be loaded last. Due to parameters.
   *
   * @private
   * @type {game.TicTacToe}
   */
  this.board_ = new game.TicTacToe(baseApiUrl, this.pubSub_, this.topic_);
};

/**
 * Default handler for all PubSub subscription events. If a turn change is
 * published to the subscriber, this will check for the computer's turn and
 * determine the best move for the computer.
 *
 * @param {Object} game_state Object containing the current game state from
 *     the PubSub event.
 * @private
 */
game.Play.prototype.determineNextMove_ = function(game_state) {
  // Set each player's token for use in board scoring.
  this.me_ = game_state.tokens.computer;
  this.opponent_ = game_state.tokens.player;

  if (game_state.status == 'in_progress' &&
    this.me_ == game_state.tokens.current_turn) {

    var nextMove = this.findMoveOnBoard_(game_state.board);

    var request = this.board_.getRequestAsJson(this.board_.Actions.TAKE,
        {'player': goog.dom.getElement('current-turn').className,
         'x': nextMove.x,
         'y': nextMove.y});
    this.board_.sendRequest(goog.string.hashCode(request), request);
  }
};

/**
 * Finds the most advantageous cell to take on a Tic-Tac-Toe board.
 * Accomplishes this by using this class's minimax implementation with a small
 * depth to limit the look-ahead prediction of the algorithm.
 *
 * @param {Array.<Array.<string>>} board 2D array representing a Tic-Tac-Toe
 *     board.
 * @private
 * @return {Obect.<string, number} Object containing the X and Y-axis
 *     coordinates to take.
 */
game.Play.prototype.findMoveOnBoard_ = function(board) {
  /**
   * Different checks due to differing initial board state between the game
   * resetting and being initalized for the first time.
   */
  if (board.length == 0 || board[1][1] == 'empty') {
    return {'x': 1, 'y': 1};
  }

  // 1000 chosen as max score for any player could only be 800
  move = this.minimax_(
      board, goog.dom.getElement('current-turn').className, -1000, 1000, 2);
  return {'x': move.x, 'y': move.y};
};

/**
 * Generate a score for the board's diagonal cells.
 * @param {Array.<Array.<string>>} board Tic-Tac-Tac board for which to find
 *     the score.
 * @private
 * @return {number} Combined score for both diagonals on the board.
 */
game.Play.prototype.getDiagonalScore_ = function(board) {
  var leftDiagonalTokens = []; // Diagonal cells from top-left to bottom-right.
  var rightDiagonalTokens = []; // Diagonal cells from top-right to bottom-left.

  for (var i = 0, j = 2; i < board.length; i++, j--) {
    leftDiagonalTokens.push(board[i][i]);
    rightDiagonalTokens.push(board[i][j]);
  }

  return this.getScoreFromTokens_(leftDiagonalTokens) +
      this.getScoreFromTokens_(rightDiagonalTokens);
};

/**
 * Gets the position of each empty cell on the board.
 * @param {Array.<Array.<string>>} board Tic-Tac-Tac board for which to find
 *     empty cells.
 * @private
 * @return {Array} Array of objects containing the X and Y-axis coordinates
 *     of all empty cells.
 */
game.Play.getEmptyCells_ = function(board) {
  var cells = [];
  for (var j = 0; j < board.length; j++) {
    for (var i = 0; i < board[j].length; i++) {
      if (board[i][j] == 'empty') {
        cells.push({'x': i, 'y': j});
      }
    }
  }
  return cells;
};

/**
 * Generate a score for the board's rows and columns.
 * @param {Array.<Array.<string>>} board Tic-Tac-Tac board for which to find
 *     the score.
 * @private
 * @return {number} Combined score for all rows and columns.
 */
game.Play.prototype.getNonDiagonalScore_ = function(board) {
  var row = [];
  var column = [];
  var score = 0;

  for (var j = 0; j < board.length; j++) {
    for (var i = 0; i < board[j].length; i++) {
      row.push(board[i][j]);
      column.push(board[j][i]);
    }
    score += this.getScoreFromTokens_(row) + this.getScoreFromTokens_(column);
    row = [];
    column = [];
  }
  return score;
};

/**
 * Returns the score for any 3-series of cells. The scoring is based on orders
 * of magnitude of 10 such that:
 * <ul>
 *   <li>Any series with a single token is scored as 1</li>
 *   <li>Any series with a two equivalent tokens is scored as 10</li>
 *   <li>Any series with a two equivalent token  is scored as 100</li>
 *   <li>Otherwise, the series is scored as a 0</li>
 * </ul>
 *
 * This scoring magnitude places a higher value on a game state that can be
 * used to prioritize moves based  on blocking or winning the game.
 *
 * @param {Array.<string>} tokens Series of 3 cells to score.
 * @private
 * @return {number} Score for the provided series.
 */
game.Play.prototype.getScoreFromTokens_ = function(tokens) {
  var score = 0;

  if (goog.array.contains(tokens, this.me_) &&
      !goog.array.contains(tokens, this.opponent_)) {

    var tokenCount = goog.array.count(tokens, function(element) {
      return element == this.me_;
    }, this);

    // Subtract 1 to keep score from quickly diverging from the 0-score.
    score = Math.pow(10, tokenCount - 1);
  } else if (!goog.array.contains(tokens, this.me_) &&
             goog.array.contains(tokens, this.opponent_)) {

    var tokenCount = goog.array.count(tokens, function(element) {
      return element == this.opponent_;
    }, this);

    // Negative score to differentiate computer v. human score.
    score = -Math.pow(10, tokenCount - 1);
  }
  return score;
};

/**
 * Generates a total score for the given game board.
 * @param {Array.<Array.<string>>} board 2D array representating the state
 *     of a Tic-Tac-Toe board.
 * @private
 * @return {number} Total score for the given game state.
 */
game.Play.prototype.generateHeuristics_ = function(board) {
  return this.getNonDiagonalScore_(board) + this.getDiagonalScore_(board);
};

/**
 * Initializes the class by subscriping to the game's PubSub channel and
 * gathering all the nodes that require an event listener.
 *
 * @param {Array} nodes Array of DOM nodes to initalize within the game board.
 */
game.Play.prototype.init = function(nodes) {
  this.pubSub_.subscribe(this.topic_, this.determineNextMove_, this);

  this.board_.init(nodes, goog.dom.getElement('new-game'));
};

/**
 * Builds a subset of the total game tree to determine the best cell to take
 * next. Based on the Minimax with Alpha-Beta pruning algorithm
 * (http://en.wikipedia.org/wiki/Alpha-beta_pruning), this attempts to
 * minimize the opponent's score while maximing the player's own score.
 *
 * The alpha-beta pruning eliminates exploring uncessary branches. Within the
 * modified minimax algortihm, if a >= b, then no subbranches from this point
 * will yield a beneficial score.
 *
 * @param {Array.<Array.<string>>} board 2D array of the changing board state
 *     throughout the recursion process.
 * @param {string} player The player to either minimize or maximize the score.
 * @param {number} alpha Minimum score of the maximizing player.
 * @param {number} beta Maximum score of the minimizing player.
 * @param {number} depth The maximum depth of the leaves to explore on the
 *     game tree.
 * @private
 * @return {Object.<string, number>} The best score found in the game tree
 *     plus the X and Y coordinates of the cell resulting in the best outcome.
 */
game.Play.prototype.minimax_ = function(board, player, alpha, beta, depth) {
  var availableCells = game.Play.getEmptyCells_(board);

  var bestX = -1;
  var bestY = -1;
  var score;

  if (availableCells.length == 0 || depth == 0) {
    return {'score': this.generateHeuristics_(board)};
  } else {
    for (var i = 0; i < availableCells.length; i++) {
      var cell = availableCells[i];
      board[cell.x][cell.y] = player;

      /**
       * With the opponent being the minimizing player, this will result in
       * the computer choosing to block the opponent's win over taking it's
       * own win.
       */
      if (player == this.opponent_) {
        score = this.minimax_(board, this.me_, alpha, beta, depth - 1);
        if (score.score < beta) {
          beta = score.score;
          bestX = cell.x;
          bestY = cell.y;
        }
      } else {
        score = this.minimax_(board, this.opponent_, alpha, beta, depth - 1);
        if (score.score > alpha) {
          alpha = score.score;
          bestX = cell.x;
          bestY = cell.y;
        }
      }
      board[cell.x][cell.y] = 'empty';
      if (alpha >= beta) {
        break;
      }
    }
    return {'score': (player == this.opponent_) ?
        beta : alpha, 'x': bestX, 'y': bestY};
  }
};

// Get all of the cells in the TicTacToe board to attach CLICK listeners.
var nodes = goog.array.concat(
    goog.array.slice(goog.dom.getElementsByClass('top'), 0),
    goog.array.slice(goog.dom.getElementsByClass('center'), 0),
    goog.array.slice(goog.dom.getElementsByClass('bottom'), 0));

var play = new game.Play('/rpc', 'tictactoe');
play.init(nodes);
