import random
import os
import sys

GRID_SIZE = 10
SHIPS_SIZES = {"aircraft carrier": 5, 
              "battleship": 4, 
              "cruiser": 3, 
              "submarine": 3, 
              "destroyer": 2}
SHIPS_NAMES = ["aircraft carrier", "battleship", "cruiser", "submarine", "destroyer"]
STR_TO_INT = {"A":0,"B":1,"C":2,"D":3,"E":4,"F":5,"G":6,"H":7,"I":8,"J":9}
INT_TO_STR = {0:"A",1:"B",2:"C",3:"D",4:"E",5:"F",6:"G",7:"H",8:"I",9:"J"}
PIECE_CHAR = '#'

def clear_console():
  os.system('cls' if os.name == 'nt' else 'clear')

# Takes any input from the user and makes sure it is a coordinate
#  returns (-1,-1) if the input is bad
#  otherwise returns integer coordinate version of the input
def input_to_coordinate(player_input: str) -> tuple[int, int]:
  # Remove whitespace and make the coordinate upperspace
  player_input = player_input.replace(" ", "").upper()
  # Check that the length of the string is 2
  if len(player_input) != 2: return (-1,-1)
  # Check that the first character is a letter
  if not player_input[0].isalpha(): return (-1,-1)
  # Check that the second character is a number
  if not player_input[1].isdigit(): return (-1,-1)
  # Checks that the input is not out of bounds for the STR_TO_INT dictionary
  if player_input[0] > "J": return (-1,-1)
  col, row = (STR_TO_INT[player_input[0]], int(player_input[1]))
  # Check that the entry is within the grid
  if col not in range(10) and row not in range(10): return (-1,-1)
  return (col, row)

# Holds all information about a player's board
class BoardState:
  # state represents a player's view of their own board
  # fog_of_war represents a player's view of their opponent's board
  # ships will be an array of arrays, each array holding the grid locations of each segment of each ship
  #  this is to determine when one player destroys one of their opponent's ships
  # ships_dict will have a ship name key to access the grid locations of the key ship
  #  this is to know the name of the ship that is destroyed so that the name can be
  # ships_remaining will contain the names of ships that have yet to be sunk
  def __init__(self, state=None, fog_of_war=None, ships=None, ships_dict=None, ships_remaining=None):
    self.state = state if state is not None else [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.fog_of_war = fog_of_war if fog_of_war is not None else [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.ships = ships if ships is not None else []
    self.ships_dict = {} if ships_dict is None else {k: v[:] for k, v in ships_dict.items()}
    self.ships_remaining = list(SHIPS_NAMES) if ships_remaining is None else list(ships_remaining)
  
  """SHIP PLACEMENT HELPERS"""
  # Takes coordinate and ship size, returns list of possible swing coordinates as strings
  #  Example return: ["A0", "J4", "B2"]
  def get_allowed_swing_points(self, anchor_row: int, anchor_col: int, ship_size: int) -> list[str]:
    possible_positions = []
    swing_down_allowed = swing_right_allowed = swing_up_allowed = swing_left_allowed = False

    # The offset of 1 accounts for only needing to be ship_size-1 spots away from the anchor
    right_swing_point = anchor_col+(ship_size-1)
    down_swing_point = anchor_row+(ship_size-1)
    left_swing_point = anchor_col-(ship_size-1)
    up_swing_point = anchor_row-(ship_size-1)
    
    # If down swing is in the grid
    # swing_down_allowed is set to true if all grid spaces from the anchor to swing point are ~
    if (down_swing_point <= 9): swing_down_allowed = all(self.state[n][anchor_col] == '~' for n in range(anchor_row+1, down_swing_point+1))
    # If right swing is in the grid
    # swing_right_allowed is set to true if all grid spaces from the anchor to swing point are ~
    if (right_swing_point <= 9): swing_right_allowed = all(self.state[anchor_row][n] == '~' for n in range(anchor_col+1, right_swing_point+1))
    # If up swing is in the grid
    # swing_up_allowed is set to true if all grid spaces from the anchor to swing point are ~
    if (up_swing_point >= 0): swing_up_allowed = all(self.state[n][anchor_col] == '~' for n in range(up_swing_point, anchor_row))
    # If left swing is in the grid
    # swing_left_allowed is set to true if all grid spaces from the anchor to swing point are ~
    if (left_swing_point >= 0): swing_left_allowed = all(self.state[n][anchor_col] == '~' for n in range(left_swing_point, anchor_col))

    # Append swing locations depending on if they are allowed
    if (swing_down_allowed): possible_positions.append(INT_TO_STR[down_swing_point] + str(anchor_col))
    if (swing_right_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(right_swing_point))
    if (swing_up_allowed): possible_positions.append(INT_TO_STR[up_swing_point] + str(anchor_col))
    if (swing_left_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(left_swing_point))

    return possible_positions
  # Prompt user to enter an anchor point for ship placement, returns tuple of grid coordinates
  #  Example return: (2,4)
  def get_anchor_point(self, ship: str) -> tuple[int, int]:
    anchor_point = None # Will hold a string ex. "A0"
    # Place anchor point
    while anchor_point == None:
      # Print statements
      clear_console()
      self.print_grid(fog_of_war=False)
      print("Choose an anchor point (ex. A1) for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
      player_choice = input("Enter your choice here: ")
      # Check input
      input_coordinate = input_to_coordinate(player_choice)
      # If bad input, reset the choosing process
      if input_coordinate == (-1,-1): continue
      # If the anchor is allowed, set it (break the loop)
      if self.state[input_coordinate[0]][input_coordinate[1]] == '~':
        anchor_point = input_coordinate
    return anchor_point
  # Prompt user to enter a swing point for ship orientation, returns tuple of grid coordinates
  #  Example return: (5,1)
  def get_swing_point(self, ship: str, valid_swing_points) -> tuple[int, int]:
    # Will hold a string version of the coordinate ex. "A0"
    swing_point = None
    # Place swing points
    while (swing_point == None):
      # Print statements
      clear_console()
      self.print_grid(fog_of_war=False)
      print("Choose a second point for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
      print("The options are: " + " ".join(valid_swing_points))
      player_choice = input("Enter your choice here: ")
      # Check input
      input_coordinate = input_to_coordinate(player_choice)
      # If bad input, reset the choosing process
      if input_coordinate == (-1,-1): continue
      # If the secondary point is allowed, set it (break the loop)
      if (INT_TO_STR[input_coordinate[0]] + str(input_coordinate[1]) in valid_swing_points): 
        swing_point = input_coordinate
    return swing_point

  """SHIP PLACEMENT"""
  # Place down a single ship
  def place_ship(self, ship: str) -> None:
    # Breaks when a ship is placed
    while True:
      # Prompt user to choose an anchor point
      anchor_row, anchor_col = self.get_anchor_point(ship)
      # Get allowed swing points (orientations that are in bounds and do not overlap other ships) from the chosen anchor
      valid_swing_points = self.get_allowed_swing_points(anchor_row, anchor_col, SHIPS_SIZES[ship])
      # If there are no possible swing points from the chosen anchor, then reset anchor
      if len(valid_swing_points) == 0: continue
      # Place the anchor point on the board
      self.state[anchor_row][anchor_col] = PIECE_CHAR
      # Prompt user to choose a swing point
      swing_row, swing_col = self.get_swing_point(ship, valid_swing_points)
      # Place ship onto board, set ship_coordinates to list of grid locations that ship was placed into
      ship_coordinates = self.write_ship_to_board(anchor_row, anchor_col, swing_row, swing_col)
      # Append list of coordinates to ships array
      self.ships.append(ship_coordinates)
      # Append {ship_name: ship_coordinates} to dictionary
      self.ships_dict.update({ship: ship_coordinates})
      # Ship successfully placed onto board
      break
  # Randomly place down a single ship
  def randomly_place_ship(self, ship: str) -> None:
    # Until the ship is properly placed
    while True:
      # Get a coordinate value not on top of a ship
      coordinate_value = '#'
      while coordinate_value == '#':
        random_row = random.randint(0, GRID_SIZE - 1)
        random_col = random.randint(0, GRID_SIZE - 1)
        coordinate_value = self.state[random_row][random_col]
      # Ensured to NOT be on top of a currently placed ship
      anchor_row, anchor_col = (random_row, random_col)
      # Get allowed swing points (orientations that are in bounds and do not overlap other ships) from the chosen anchor
      valid_swing_points = self.get_allowed_swing_points(anchor_row, anchor_col, SHIPS_SIZES[ship])
      # If there are no possible swing points from the chosen anchor, then reset anchor
      if len(valid_swing_points) == 0: continue
      # Place the anchor point on the board
      self.state[anchor_row][anchor_col] = PIECE_CHAR
      # Set secondary point (orientations that are in bounds and do not overlap other ships)
      swing_point = valid_swing_points[random.randint(0, len(valid_swing_points) - 1)]
      swing_row, swing_col = (STR_TO_INT[swing_point[0]], int(swing_point[1]))
      # Place ship onto board, set ship_coordinates to list of grid locations that ship was placed into
      ship_coordinates = self.write_ship_to_board(anchor_row, anchor_col, swing_row, swing_col)
      # Append list of coordinates to ships array
      self.ships.append(ship_coordinates)
      # Append {ship_name: ship_coordinates} to dictionary
      self.ships_dict.update({ship: ship_coordinates})
      # Ship successfully placed onto board
      break

  """MISC FUNCTIONS"""
  # Write the ship's characters onto the board
  #  a_x and a_y represent anchor coordinate, s_x and s_y represent swing coordinate
  def write_ship_to_board(self, a_x: int, a_y: int, s_x: int, s_y: int) -> None:
    # Will hold all coordinates of the ship being written to the board
    ship_coordinates = []
    # Horizontal orientation
    if a_y == s_y: 
      for x in range(min(a_x, s_x), max(a_x, s_x)+1):
        self.state[x][a_y] = PIECE_CHAR
        ship_coordinates.append([x,a_y])
    # Vertical orientation
    if a_x == s_x:
      for y in range(min(a_y, s_y), max(a_y, s_y)+1):
        self.state[a_x][y] = PIECE_CHAR
        ship_coordinates.append([a_x,y])
    return ship_coordinates
  # Check if a ship has been sunk based on previous move
  #  returns the name of the sunk ship, if no sinks returns an empty string
  def check_ship_sunk(self) -> str:
    # For each pair of name and locations of ships (goes through all ships)
    for ship_name, ship_locations in self.ships_dict.items():
      # If the ship has been sunk
      if all(self.state[row][col] == 'X' for row, col in ship_locations):
        del self.ships_dict[ship_name]
        self.ships_remaining.remove(ship_name)
        return ship_name
    return ""
  # Add labels to the board representation
  def print_grid(self, fog_of_war: bool) -> None:
    col_titles = [' '] + [str(i) for i in range(GRID_SIZE)]
    row_titles = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    if fog_of_war: print(" ".join(col_titles) + "\n" + "\n".join([row_titles[i] + " " + " ".join(self.fog_of_war[i]) for i in range(GRID_SIZE)]))
    else: print(" ".join(col_titles) + "\n" + "\n".join([row_titles[i] + " " + " ".join(self.state[i]) for i in range(GRID_SIZE)]))
  
  """MOVE OPTIONS"""
  # Choose a coordinate to attack
  #  returns a boolean, True for ship hit or False for ship not hit
  def player_move(self) -> bool:
    strike_choice = None
    while strike_choice == None:
      # Print statements
      player_choice = input("Enter your move here: ")
      input_coordinate = input_to_coordinate(player_choice)
      # Process strike choice
      if input_coordinate == (-1,-1): continue
      strike_row, strike_col = input_coordinate
      if self.fog_of_war[strike_row][strike_col] != '~': continue
      else: strike_choice = (strike_row, strike_col)
    # Check if the strike hit or missed, X for hit and O for miss on both the fog of war for enemy display and state for self display
    if self.state[strike_row][strike_col] == '#': 
      self.fog_of_war[strike_row][strike_col] = 'X'
      self.state[strike_row][strike_col] = 'X'
      return True
    if self.state[strike_row][strike_col] == '~': 
      self.fog_of_war[strike_row][strike_col] = 'O'
      self.state[strike_row][strike_col] = 'O'
      return False
  # Make a random move on the board
  #  returns a boolean, True for ship hit or False for ship not hit
  def random_move(self) -> bool:
    while True:
      random_row = random.randint(0, GRID_SIZE - 1)
      random_col = random.randint(0, GRID_SIZE - 1)
      # Checks fog of war grid to see if the location has yet to be chosen
      if self.state[random_row][random_col] not in ('X', 'O'):
        if self.state[random_row][random_col] == '#':           
          self.fog_of_war[random_row][random_col] = 'X'
          self.state[random_row][random_col] = 'X'
          return True
        if self.state[random_row][random_col] == '~': 
          self.fog_of_war[random_row][random_col] = 'O'
          self.state[random_row][random_col] = 'O'
          return False

  # Choose a coordinate to attack based on a simulated human style of play (using the even strategy)
  #  returns a boolean, True for ship hit or False for ship not hit
  def human_sim_move(self) -> None:
    raise NotImplementedError("This function will simulate a human style of play")
    while True:
      rand
  
  # Chooses a move based on Monte Carlo Tree Search
  #  returns a boolean, True for ship hit or False for ship not hit
  def AI_mcts_move(self) -> None:
    raise NotImplementedError("This function will choose a move based on Monte Carlo Tree Search")

def main():
  # Initialize the player grid
  player_grid = BoardState()
  ships_placed = False
  aiSelect = input("1 for random, 2 for even player:")
  if(aiSelect == "2"):
    sys.exit("2 not implemented")

  while ships_placed == False:
    place_own_ships = input("Would you like to place your own ships (y/n): ")
    # If the player wants to place their own ships
    if place_own_ships in ("y", "Y", "Yes", "yes"): 
      for ship_name in SHIPS_NAMES: player_grid.place_ship(ship_name)
      ships_placed = True
    # If the player wants to a randomly generated layout
    if place_own_ships in ("n", "N", "No", "no"):
      for ship_name in SHIPS_NAMES: player_grid.randomly_place_ship(ship_name)
      ships_placed = True
  
  # Initialize the adversary grid
  AI_grid = BoardState()
  for ship_name in SHIPS_NAMES:
    AI_grid.randomly_place_ship(ship_name)

  # These messages will appear at the top of the screen during each turn,
  #  so before the first turn there will be some help messages
  player_move_result = "Your board is on top and will be updated as your opponent makes moves."
  AI_move_result = "Your moves will appear on the bottom board."

  # Track number of moves for each player
  count_player = 0
  count_AI = 0

  # Run turns of the game until someone wins
  while True:
    # Show results of previous turn (or help messages if on first turn)
    clear_console()
    print(player_move_result)
    print(AI_move_result)
    # Show both grids to player with proper fog of war
    print("Your grid")
    player_grid.print_grid(fog_of_war=False)
    print("Enemy grid")
    AI_grid.print_grid(fog_of_war=True)
    # Player move executed on opponent's board
    AI_check_ship_hit = AI_grid.player_move()
    player_move_result = "You hit an enemy ship!" if AI_check_ship_hit else "You missed."
    # Check if an enemy ship has been sunk from the player's previous move
    AI_ship_sunk = AI_grid.check_ship_sunk()
    player_move_result = "You sunk the enemy " + AI_ship_sunk + "!" if AI_ship_sunk != "" else player_move_result
    count_player += 1
    # Check if the player has won
    if len(AI_grid.ships_remaining) == 0: 
      clear_console()
      print("YOU WON")
      print("It took you " + str(count_player) + " moves to win.")
      print("Your grid")
      player_grid.print_grid(fog_of_war=False)
      print("Enemy grid")
      AI_grid.print_grid(fog_of_war=True)
      break
    #player_check_ship_hit = None;  
    if(aiSelect == "1"):
      player_check_ship_hit = player_grid.random_move()
    else:
      sys.exit("invalid choice")
    
    AI_move_result = "The enemy has hit one of your ships!" if player_check_ship_hit else "The enemy missed."
    # Check if a friendly ship has been sunk from the opponent's previous move
    player_ship_sunk = player_grid.check_ship_sunk()
    AI_move_result = "The enemy has sunk your " + player_ship_sunk + "!" if player_ship_sunk != "" else AI_move_result
    count_AI += 1
    # Check if the opponent has won
    if len(player_grid.ships_remaining) == 0: 
      clear_console()
      print("YOU LOST")
      print("It took the AI " + str(count_AI) + " moves to win.")
      print("Your grid")
      player_grid.print_grid(fog_of_war=False)
      print("Enemy grid")
      AI_grid.print_grid(fog_of_war=True)
      break

if __name__ == "__main__":
  main()
