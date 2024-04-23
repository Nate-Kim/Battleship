import random
import os

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
def input_to_coordinate(player_input: str):
  # Remove whitespace and make the coordinate upperspace
  player_input = player_input.replace(" ", "").upper()
  # Check that the length of the string is 2
  if len(player_input) != 2: return (-1,-1)
  # Check that the first character is a letter
  if not player_input[0].isalpha(): return (-1,-1)
  # Check that the second character is a number
  if not player_input[1].isdigit(): return (-1,-1)
  col, row = (STR_TO_INT[player_input[0]], int(player_input[1]))
  # Check that the entry is within the grid
  if col not in range(10) and row not in range(10): return (-1,-1)
  return (col, row)

class BoardState:
  # state and fog_of_war are initialized to a 10x10 2D-array of tilde's 
  # fog_of_war represents one player's view of their opponent's board
  def __init__(self, state=None, fog_of_war=None):
    if state is None: state = [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    if fog_of_war is None: fog_of_war = [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.state = state
    self.fog_of_war = fog_of_war
  
  # Takes coordinate and ship size, returns list of possible swing coordinates as strings, eg. "A0"
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
    if (left_swing_point >= 0): swing_left_allowed = all(self.state[n][anchor_col] == '~' for n in range(up_swing_point, anchor_row))

    # Append swing locations depending on if they are allowed
    if (swing_down_allowed): possible_positions.append(INT_TO_STR[down_swing_point] + str(anchor_col))
    if (swing_right_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(right_swing_point))
    if (swing_up_allowed): possible_positions.append(INT_TO_STR[up_swing_point] + str(anchor_col))
    if (swing_left_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(left_swing_point))

    return possible_positions

  # Place down a single ship
  def place_ship(self, ship: str):
    anchor_point = None # Will hold a string ex. "A0"
    swing_point = None # Will hold a string ex. "A0"

    # Breaks when a ship is placed
    while True:
      # Place anchor point
      while anchor_point == None:
        # Print statements
        clear_console()
        self.print_grid(fog_of_war=False)
        print("Choose an anchor point (ex. A1) for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
        player_choice = input("Enter your choice here: ")
        # Check input
        input_coordinate = input_to_coordinate(player_choice)
        # If bad input, continue
        if input_coordinate == (-1,-1): continue
        if self.state[input_coordinate[0]][input_coordinate[1]] != '~': continue
        # Else set the anchor point, breaking the while loop
        anchor_point = input_coordinate
      anchor_row, anchor_col = (anchor_point[0], anchor_point[1])
      # Get allowed swing points (orientations that are in bounds and do not overlap other ships) from the chosen anchor
      valid_swing_points = self.get_allowed_swing_points(anchor_row, anchor_col, SHIPS_SIZES[ship])
      # If there are no possible swing points from the chosen anchor, then reset anchor
      if len(valid_swing_points) == 0: 
        anchor_point = None
        continue
      # Place the anchor point on the board
      self.state[anchor_row][anchor_col] = PIECE_CHAR
      while (swing_point == None):
        # Print statements
        clear_console()
        self.print_grid(fog_of_war=False)
        print("Choose a second point for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
        # TO-DO: make it possible to reset the anchor (maybe 00 -> reset anchor)
        print("The options are: " + " ".join(valid_swing_points))
        player_choice = input("Enter your choice here: ")
        # Check input
        input_coordinate = input_to_coordinate(player_choice)
        # If bad input, continue
        if input_coordinate == (-1,-1): continue
        # If the secondary point is allowed
        if (INT_TO_STR[input_coordinate[0]] + str(input_coordinate[1]) in valid_swing_points): swing_point = input_coordinate
      swing_row, swing_col = (swing_point[0], swing_point[1])
      # Place ship onto board
      # Anchor and swing x & y aliases
      a_x, a_y = (anchor_row, anchor_col)
      s_x, s_y = (swing_row, swing_col)
      if a_y == s_y:  # Horizontal orientation
        for x in range(min(a_x, s_x), max(a_x, s_x)+1):
          self.state[x][a_y] = PIECE_CHAR
      if a_x == s_x:  # Vertical orientation
        for y in range(min(a_y, s_y), max(a_y, s_y)+1):
          self.state[a_x][y] = PIECE_CHAR
      # Ship successfully placed onto board
      break

  # Choose a coordinate to attack
  #  returns a string depending on whether the move hit a ship
  def player_move(self) -> str:
    strike_choice = None

    while strike_choice == None:
      # Print statements
      print("Enemy grid")
      self.print_grid(fog_of_war=True)
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
      return "You hit an opponent ship!"
    if self.state[strike_row][strike_col] == '~': 
      self.fog_of_war[strike_row][strike_col] = 'O'
      self.state[strike_row][strike_col] = 'O'
      return "You missed."

  # Make a random move on the board
  #  returns a string depending on whether the move hit a ship
  def random_move(self) -> str:
    while True:
      random_row = random.randint(0, GRID_SIZE - 1)
      random_col = random.randint(0, GRID_SIZE - 1)
      # Checks fog of war grid to see if the location has yet to be chosen
      if self.fog_of_war[random_row][random_col] == '~':
        if self.state[random_row][random_col] == '#':           
          self.fog_of_war[random_row][random_col] = 'X'
          self.state[random_row][random_col] = 'X'
          return "The opponent hit one of your ships!"
        if self.state[random_row][random_col] == '~': 
          self.fog_of_war[random_row][random_col] = 'O'
          self.state[random_row][random_col] = 'O'
          return "The opponent missed."
        break

  # Return a random anchor coordinate as string ex. "A0"
  def random_coordinate(self):
    coordinate_value = '#'
    while coordinate_value == '#':
      random_row = random.randint(0, GRID_SIZE - 1)
      random_col = random.randint(0, GRID_SIZE - 1)
      coordinate_value = self.state[random_row][random_col]
    return INT_TO_STR[random_row] + str(random_col)

  # Randomly place down a single ship
  def randomly_place_ship(self, ship: str):
    anchor_point = None
    swing_point = None

    # Until the ship is properly placed
    while True:
      # Ensured to NOT be on top of a currently placed ship
      anchor_point = self.random_coordinate()
      anchor_coordinate_info = input_to_coordinate(anchor_point)
      if anchor_coordinate_info == (-1,-1): continue
      # Place the anchor point on the board
      anchor_row, anchor_col = (anchor_coordinate_info[0], anchor_coordinate_info[1])
      self.state[anchor_row][anchor_col] = PIECE_CHAR
      # Get allowed swing points (orientations that are in bounds and do not overlap other ships) from the chosen anchor
      valid_swing_points = self.get_allowed_swing_points(anchor_row, anchor_col, SHIPS_SIZES[ship])
      # If there are no possible swing points from the chosen anchor, then reset anchor
      if len(valid_swing_points) == 0: continue
      # Set secondary point (orientations that are in bounds and do not overlap other ships)
      swing_point = valid_swing_points[random.randint(0, len(valid_swing_points) - 1)]
      swing_row, swing_col = (STR_TO_INT[swing_point[0]], int(swing_point[1]))
      
      # Anchor and swing x & y aliases, all in integer form
      a_x, a_y = (anchor_row, anchor_col)
      s_x, s_y = (swing_row, swing_col)
      if a_y == s_y:  # Horizontal orientation
        for x in range(min(a_x, s_x), max(a_x, s_x)+1):
          self.state[x][a_y] = PIECE_CHAR
      if a_x == s_x:  # Vertical orientation
        for y in range(min(a_y, s_y), max(a_y, s_y)+1):
          self.state[a_x][y] = PIECE_CHAR
      # Place ship randomly
      break

  # Add labels to the board representation
  def print_grid(self, fog_of_war: bool):
    col_titles = [' '] + [str(i) for i in range(GRID_SIZE)]
    row_titles = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    if fog_of_war:
      print(" ".join(col_titles) + "\n" + "\n".join([row_titles[i] + " " + " ".join(self.fog_of_war[i]) for i in range(GRID_SIZE)]))
    else:
      print(" ".join(col_titles) + "\n" + "\n".join([row_titles[i] + " " + " ".join(self.state[i]) for i in range(GRID_SIZE)]))

def main():
  player_grid = BoardState()
  for ship in SHIPS_NAMES:
    player_grid.place_ship(ship)
  AI_grid = BoardState()
  for ship in SHIPS_NAMES:
    AI_grid.randomly_place_ship(ship)

  # These messages will appear at the top of the screen during each turn,
  #  so before the first turn there will be some help messages
  player_move_result = "Your board is on top and will be updated as your opponent makes moves."
  AI_move_result = "Your moves will appear on the bottom board."

  while True:
    clear_console()
    # Show results of previous turn
    print(player_move_result)
    print(AI_move_result)
    # Show own grid to player
    print("Your grid")
    player_grid.print_grid(fog_of_war=False)
    # Player move executed on opponent's board
    # This also shows opponent's grid with fog of war
    player_move_result = AI_grid.player_move() 
    AI_move_result = player_grid.random_move()

if __name__ == "__main__":
  main()