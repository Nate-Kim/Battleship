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

# Takes a coordinate and ensures it lies in board range
def coordinate_in_board(row: int, col: int) -> bool:
  # Checks that the entry is within the grid
  if (col in range(10) and row in range(10)): 
    return True
  return False

# Takes coordinate (ex. "A0") and returns (0, 0)
#  if the first character is not a letter, it becomes -1 (gets caught by validate_anchor_placement())
#  if the second character is not a number, it becomes -1 (gets caught by validate_anchor_placement())
def input_to_coordinate(player_input: str):
  if player_input[0].isalpha(): row = STR_TO_INT[player_input[0]]
  else: row = -1
  if player_input[1].isdigit(): col = int(player_input[1])
  else: col = -1
  return (row, col)

class BoardState:
  # State is initialized to a 10x10 2D-array of tilde's 
  def __init__(self, state=[['~'] * GRID_SIZE for _ in range(GRID_SIZE)]):
    self.state = state

  # Place a PIECE_CHAR on a given grid space to act as anchor
  #  returns the same board if the space is already taken
  def place_anchor(self: "BoardState", anchor_row: int, anchor_col: int) -> "BoardState":
    if (self.state[anchor_row][anchor_col] == '#'):
      return self
    self.state[anchor_row][anchor_col] = PIECE_CHAR
    return self
  
  # Takes coordinate and ship size, returns list of possible swing coordinates as strings, eg. "A0"
  def get_allowed_swing_points(self, anchor_row: int, anchor_col: int, ship_size: int) -> list[str]:
    possible_positions = []
    swing_down_allowed = swing_right_allowed = swing_up_allowed = swing_left_allowed = True

    # The offset of 1 accounts for only needing to be ship_size-1 spots away from the anchor
    right_swing_point = anchor_col+(ship_size-1)
    down_swing_point = anchor_row+(ship_size-1)
    left_swing_point = anchor_col-(ship_size-1)
    up_swing_point = anchor_row-(ship_size-1)
    
    # If down swing is in the grid
    if (down_swing_point <= 9): 
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(anchor_row+1, down_swing_point+1): # Don't want to count anchor as a different ship
        if (self.state[n][anchor_col] != '~'):
          swing_down_allowed = False
    else: 
      swing_down_allowed = False

    # If right swing is in the grid
    if (right_swing_point <= 9):
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(anchor_col+1, right_swing_point+1):
        if (self.state[anchor_row][n] != '~'):
          swing_right_allowed = False
    else: 
      swing_right_allowed = False

    # If up swing is in the grid
    if (up_swing_point >= 0): 
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(up_swing_point, anchor_row):
        if (self.state[n][anchor_col] != '~'):
          swing_up_allowed = False
    else: 
      swing_up_allowed = False

    # If left swing is in the grid
    if (left_swing_point >= 0): 
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(left_swing_point, anchor_col):
        if (self.state[anchor_row][n] != '~'):
          swing_left_allowed = False
    else: 
      swing_left_allowed = False

    if (swing_down_allowed): possible_positions.append(INT_TO_STR[down_swing_point] + str(anchor_col))
    if (swing_right_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(right_swing_point))
    if (swing_up_allowed): possible_positions.append(INT_TO_STR[up_swing_point] + str(anchor_col))
    if (swing_left_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(left_swing_point))
    return possible_positions

  # Place down a single ship
  def place_ship(self, ship: str):
    anchor_point = None # String ex. "A1"
    swing_point = None # String ex. "A1"
    invalid_no_swings = False
    invalid_not_two_chars = False
    while True:
      # Place anchor point
      while anchor_point == None:
        clear_console()
        if invalid_no_swings: print("Invalid anchor point.")
        if invalid_not_two_chars: print("Not a grid coordinate.")
        print(self)
        print("Choose an anchor point (ex. A1) for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
        player_choice = input("Enter your choice here: ")
        # Check input length
        if (len(player_choice.strip()) != 2): 
          invalid_not_two_chars = True
          continue
        # Check input validity
        anchor_coordinate_info = input_to_coordinate(player_choice.upper().strip())
        if (coordinate_in_board(anchor_coordinate_info[0], anchor_coordinate_info[1])):
          anchor_point = player_choice

      # Place the anchor point on the board
      self.place_anchor(anchor_coordinate_info[0], anchor_coordinate_info[1])
      # If there are no possible swing points from the chosen anchor
      if len(self.get_allowed_swing_points(anchor_coordinate_info[0], anchor_coordinate_info[1], SHIPS_SIZES[ship])) == 0:
        invalid_no_swings = True
        # Set the chosen anchor back to an empty space
        self.state[anchor_coordinate_info[0]][anchor_coordinate_info[1]] = '~'
        # Reset anchor point
        anchor_point = None
        continue
      clear_console()
      print(self)

      # Get possible secondary points (orientations that are in bounds and do not overlap other ships)
      allowed_swing_points = self.get_allowed_swing_points(anchor_coordinate_info[0], anchor_coordinate_info[1], SHIPS_SIZES[ship])
      while (swing_point == None):
        print("Choose a second point for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
        # TO-DO: make it possible to reset the anchor (maybe 00 -> reset anchor)
        print("The options are: " + " ".join(allowed_swing_points))
        player_choice = input("Enter your choice here: ")
        if (player_choice.upper().strip() in allowed_swing_points):
          swing_point = player_choice.upper().strip()
        else:
          clear_console()
          print("Please choose a valid secondary point.")
          print(self)

      # Place ship onto board
      swing_coordinate_info = input_to_coordinate(player_choice.upper().strip())
      # Anchor and swing x & y aliases, all in integer form
      a_x, a_y = (anchor_coordinate_info[0], anchor_coordinate_info[1])
      s_x, s_y = (swing_coordinate_info[0], swing_coordinate_info[1])
      if a_y == s_y:  # Horizontal orientation
        for x in range(min(a_x, s_x), max(a_x, s_x)+1):
          self.state[x][a_y] = PIECE_CHAR
      if a_x == s_x:  # Vertical orientation
        for y in range(min(a_y, s_y), max(a_y, s_y)+1):
          self.state[a_x][y] = PIECE_CHAR

      clear_console()
      print(self)
      break

  # Return a random anchor coordinate (for base adversary implementation)
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

    while True:
      # Ensured to NOT be on top of a currently placed ship
      anchor_point = self.random_coordinate()
      anchor_coordinate_info = input_to_coordinate(anchor_point)

      # Place the anchor point on the board
      self.place_anchor(anchor_coordinate_info[0], anchor_coordinate_info[1])
      # If there are no possible swing points from the chosen anchor
      if len(self.get_allowed_swing_points(anchor_coordinate_info[0], anchor_coordinate_info[1], SHIPS_SIZES[ship])) == 0:
        # Set the chosen anchor back to an empty space
        self.state[anchor_coordinate_info[0]][anchor_coordinate_info[1]] = '~'
        # Reset anchor point
        anchor_point = None
        continue

      # Get possible secondary points (orientations that are in bounds and do not overlap other ships)
      allowed_swing_points = self.get_allowed_swing_points(anchor_coordinate_info[0], anchor_coordinate_info[1], SHIPS_SIZES[ship])
      random_choice = allowed_swing_points[random.randint(0, len(allowed_swing_points) - 1)]
      swing_point = random_choice
      
      # Place ship onto board
      swing_coordinate_info = input_to_coordinate(swing_point)
      # Anchor and swing x & y aliases, all in integer form
      a_x, a_y = (anchor_coordinate_info[0], anchor_coordinate_info[1])
      s_x, s_y = (swing_coordinate_info[0], swing_coordinate_info[1])
      if a_y == s_y:  # Horizontal orientation
        for x in range(min(a_x, s_x), max(a_x, s_x)+1):
          self.state[x][a_y] = PIECE_CHAR
      if a_x == s_x:  # Vertical orientation
        for y in range(min(a_y, s_y), max(a_y, s_y)+1):
          self.state[a_x][y] = PIECE_CHAR
      break

  # Add labels to the board representation
  def __str__(self):
    col_titles = [' '] + [str(i) for i in range(GRID_SIZE)]
    row_titles = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    return " ".join(col_titles) + "\n" + "\n".join([row_titles[i] + " " + " ".join(self.state[i]) for i in range(GRID_SIZE)])

def main():
  player_grid = BoardState()
  for ship in SHIPS_NAMES:
    player_grid.place_ship(ship)
  AI_grid = BoardState()
  for ship in SHIPS_NAMES:
    AI_grid.randomly_place_ship(ship)

if __name__ == "__main__":
  main()