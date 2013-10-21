/**
* @fileoverview Library for contructing and manipulating a Tic-Tac-Toe game.
* Also provides connectivity to the game's RPC server.
* @author bwreher@gmail.com (Brandon Reher)
*/

goog.provide('game.TicTacToe');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.TagName');
goog.require('goog.events.Event');
goog.require('goog.events.EventHandler');
goog.require('goog.events.EventType');
goog.require('goog.json');
goog.require('goog.net.EventType');
goog.require('goog.net.XhrIo');
goog.require('goog.net.XhrManager');
goog.require('goog.pubsub.PubSub');
goog.require('goog.string');


/**
 * Library for connecting to and manipulating a basic Tic-Tac-Toe game.
 *
 * @param {string} apiUrl URL for the game server's RPC requests.
 * @param {goog.pubsub.PubSub} pubSub PubSub object to publish messages on.
 * @param {string} topic PubSub topic to reach subscribers.
 * @constructor
 */
game.TicTacToe = function(apiUrl, pubSub, topic) {
  /**
   * Actions that the RPC server recognizes.
   *
   * @enum {string}
   */
  this.Actions = {
    RESET: 'reset',
    TAKE: 'take'
  };

  /**
   * Base URL for RPC requests
   *
   * @private
   * @type {string}
   */
  this.apiUrl_ = apiUrl;

  /**
   * Nodes to toggle CLICK listeners on.
   *
   * @private
   * @type {Array}
   */
  this.cellNodes_ = [];

  /**
   * Event handler to attach listeners for the DOM events.
   *
   * @private
   * @type {goog.events.EventHandler}
   */
  this.eventHandler_ = new goog.events.EventHandler(this);

  /**
   * Map of IDs to coordinates on the grid. Necessary for direct access to
   * the container <span> elements--where the O/X tokens will be placed.
   *
   * @private
   * @type {Array.<Array.<string>>}
   */
  this.innerCellMap_ = [['tl', 'cl', 'bl'],
                        ['tm', 'cm', 'bm'],
                        ['tr', 'cr', 'br']];

  /**
   * Map of <div> class name's to the corresponding X or Y-axis coordinate.
   * Necessary to generate the coordinates of a click event in relation
   * to the Tic-Tac-Toe board.
   *
   * @private
   * @type {Object.<string, number>}
   */
  this.outerCellMap_ = goog.object.create('top', 0,
                                          'left', 0,
                                          'center', 1,
                                          'middle', 1,
                                          'bottom', 2,
                                          'right', 2);

  /**
   * PubSub object used to notify subscribers of the turn changing.
   *
   * @private
   * @type {goog.pubsub.PubSub}
   */
  this.pubSub_ = pubSub;

  /**
   * All possible states for a Tic-Tac-Toe cell.
   *
   * @enum {string}
   * @private
   */
  this.States_ = {
    EMPTY: 'empty',
    TAKEN_O: 'taken-o',
    TAKEN_X: 'taken-x'
  };

  /**
   * PubSub topic to publish.
   *
   * @private
   * @type {string}
   */
  this.topic_ = topic;

  /**
   * Xhr manager for requests to the RPC server.
   *
   * @private
   * @type {goog.net.XhrManager}
   */
  this.xhrManager_ = new goog.net.XhrManager();
};

/**
 * Removes the butterbar node from the DOM.
 * @private
 */
game.TicTacToe.prototype.clearButterBar_ = function() {
  goog.dom.removeNode(goog.dom.getElement('butterbar'));
};

/**
 * Creates a JSON-stringified request of the game action and optional payload.
 *
 * @param {string} action Game action that has been requested.
 * @param {Object.<string, number|string>=} opt_message Payload to send in
 *     the request (optional).
 * @return {string} JSON stringification of the requested action and payload.
 */
game.TicTacToe.prototype.getRequestAsJson = function(action, opt_message) {
  var request = goog.object.create('action', action);

  if (goog.isDefAndNotNull(opt_message)) {
    goog.object.extend(request, opt_message);
  }

  return JSON.stringify(request);
};

/**
 * Initializes the event listeners for the game. Attaches click listeners to
 * each Tic-Tac-Toe cell and to teh 'New Game' button.
 *
 * @param {Array.<Node>} nodes Array of (grid) nodes to attach listeners.
 * @param {Node} resetNode Node to that resets the game on click.
 */
game.TicTacToe.prototype.init = function(nodes, resetNode) {
  // Attach to each cell node.
  this.cellNodes_ = nodes;
  this.resetCellListeners_();

  // Attach to the 'New Game' button.
  this.eventHandler_.listen(
      resetNode, goog.events.EventType.CLICK, this.resetBoard_);

  var player = goog.dom.getElement('player-token').className;
  var computer = (player == this.States_.TAKEN_X) ?
      this.States_.TAKEN_O : this.States_.TAKEN_X;

  this.pubSub_.publish(this.topic_,
      {'board': [],
       'status': 'in_progress',
       'tokens': {'current_turn': goog.dom.getElement('current-turn').className,
                  'computer': computer,
                  'player': player}
      }
  );
};

/**
 * Draws the TicTacToe board based on the JSON response.
 *
 * @param {Array.<Array.<string>>} board 2D array indicating the token
 *   to apply for each TicTacToe cell at the given coordinates.
 * @private
 */
game.TicTacToe.prototype.renderGameBoard_ = function(board) {
  for (var i = 0; i < board.length; i++) {
    for (var j = 0; j < board[i].length; j++) {
      goog.dom.getElement(this.innerCellMap_[i][j]).className = board[i][j];
    }
  }
};

/**
 * Resets the CLICK listeners on the Tic-Tac-Toe board. If the keepOff option
 * is specified, the listeners will not be reattached.
 *
 * @param {boolean=} opt_keepOff Option to keep the listeners off the cells.
 * @private
 */
game.TicTacToe.prototype.resetCellListeners_ = function(opt_keepOff) {
  goog.array.every(this.cellNodes_, function(node) {
    return this.eventHandler_.unlisten(
          node, goog.events.EventType.CLICK, this.tryTakeAction_);
  }, this);

  if (!opt_keepOff) {
    goog.array.every(this.cellNodes_, function(node) {
      return this.eventHandler_.listen(
          node, goog.events.EventType.CLICK, this.tryTakeAction_);
    }, this);
  }
};

/**
 * Sends a request to the RPC server for a complete game reset. Used as a
 * responder to the click event on the 'New Game' button.
 *
 * @private
 */
game.TicTacToe.prototype.resetBoard_ = function() {
  var request = this.getRequestAsJson(this.Actions.RESET);
  this.sendRequest(goog.string.hashCode(request), request);
  this.resetCellListeners_();
};

/**
 * Send the given request to the XhrManager's queue. If the request is
 * sucessfully queued, attach an event responder to the request's completion.
 * Otherwise, write a message that the queue needs time to empty.
 *
 * @param {string} id ID for the request. Prevents the request for getting
 *     duplicate requests in the queue.
 * @param {Obect.<string, *>} request Object mapping request keys to
 *     their values.
 */
game.TicTacToe.prototype.sendRequest = function(id, request) {
  var xhrRequest = this.xhrManager_.send(id, this.apiUrl_, 'POST', request);

  if (xhrRequest) {
    this.eventHandler_.listen(xhrRequest.xhrIo, goog.net.EventType.COMPLETE,
                              this.serverResponseHandler_);
  } else {
    this.writeToButterBar_('Please wait for request queue to empty.');
  }
};

/**
 * Receives the game server's response, then updates the game board
 * and player tokens.
 *
 * @param {goog.events.Event} e Event response from the XhrIo action.
 * @private
 */
game.TicTacToe.prototype.serverResponseHandler_ = function(e) {
  if (e.target.isSuccess()) {
    this.clearButterBar_();
  } else {
    this.writeToButterBar_('Unable to connect to the server.');
    return;
  }

  var response = JSON.parse(e.target.getResponse());

  if (response.status == 'failed') {
    this.writeToButterBar_(response.message);
    return;
  } else if (response.status == 'win' || response.status == 'tie') {
    this.resetCellListeners_(true);
  }

  this.updateTokens_(response.tokens.current_turn, response.tokens.player);

  if (response.message != null) {
    this.writeToButterBar_(response.message);
  }

  this.renderGameBoard_(response.grid);
  this.pubSub_.publish(this.topic_, {'board': response.grid,
                                     'status': response.status,
                                     'tokens': response.tokens});
};

/**
 * Tries to take the clicked cell for the current player.
 *
 * First checks to see if the cell has been taken. If not, try to connect to
 * the RPC server to initiate a take action. On a successful take action, this
 * will replace the cell with the player's icon. Otherwise, this will place an
 * error message in the butterbar.
 *
 * @param {goog.event.Event} e Click event from the board.
 * @private
 */
game.TicTacToe.prototype.tryTakeAction_ = function(e) {
  if (e.target.firstChild != null) {  // Clicked on a <div>
    var divClass = e.target.className;
    var spanClass = e.target.firstChild.nextSibling;
  } else {    // Clicked on a <span>
    var divClass = e.target.parentNode.className;
    var spanClass = e.target.className;
  }

  var classNames = divClass.split(' ');

  if (spanClass === this.States_.TAKEN_O ||
      spanClass === this.States_.TAKEN_X) {
    this.writeToButterBar_('Cell already taken');
    return;
  } else if (classNames.length != 2) {
    this.writeToButterBar_('Unable to determine the location of clicked cell.');
  }

  var request = this.getRequestAsJson(this.Actions.TAKE,
      {'player': goog.dom.getElement('player-token').className,
       'x': goog.object.get(this.outerCellMap_, classNames[1], -1),
       'y': goog.object.get(this.outerCellMap_, classNames[0], -1)});

  this.sendRequest(goog.string.hashCode(request), request);
};

/**
 * Updates the current turn and human player tokens.
 *
 * @param {string} currentTurn Class designated for the current player's token.
 * @param {string} playerToken Class representing the human player's token.
 * @private
 */
game.TicTacToe.prototype.updateTokens_ = function(currentTurn, playerToken) {
  goog.dom.getElement('current-turn').className = goog.string.htmlEscape(
      currentTurn);
  goog.dom.getElement('player-token').className = goog.string.htmlEscape(
      playerToken);
};

/**
 * Creates a 'butterbar' element with the given message. This will float above
 * the game and should be reserved for errors or short notices.
 *
 * @param {string} message Message to output to the butterbar.
 * @private
 */
game.TicTacToe.prototype.writeToButterBar_ = function(message) {
  var parentContainer = goog.dom.createDom(
      goog.dom.TagName.DIV,
      {'id': 'butterbar'},
      goog.dom.createDom(goog.dom.TagName.P,
                         null,
                         goog.string.escapeString(message)));

  if (!goog.dom.getElement('butterbar')) {
    goog.dom.appendChild(
        document.getElementsByTagName('header')[0], parentContainer);
  } else {
    goog.dom.replaceNode(goog.dom.getElement('butterbar'), parentContainer);
  }
};
