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

# Takes a coordinate and ensures it lies in board range
def coordinate_in_board(c: str, i: int) -> bool:
  # Checks that the entry is within the grid
  if (i in range(10) and STR_TO_INT[c] in range(10)): 
    return True
  return False

# Takes coordinate (ex. "A1") and returns ("A", 1)
# If the second character is not a number, it becomes -1 (gets caught by validate_anchor_placement())
def coordinate_to_tuple(s: str):
  c = s[0]
  # Check if the remaining part is a number
  # If it's a number, convert it to an integer
  if s[1].isdigit(): i = int(s[1])
  else: i = -1 # Else, set to -1 so it gets caught by validate_anchor_placement()
  # Return a tuple containing the letter and the number
  return (c, i)

class BoardState:
  # State is initialized to a 10x10 2D-array of tilde's 
  def __init__(self, state=[['~'] * GRID_SIZE for _ in range(GRID_SIZE)]):
    self.state = state

  # Place a PIECE_CHAR on the (c,i) grid space
  def place_anchor(self: "BoardState", anchor_row: str, anchor_col: int) -> "BoardState":
    anchor_row_int = STR_TO_INT[anchor_row]
    if (self.state[anchor_row_int][anchor_col] == '#'):
      return self
    self.state[anchor_row_int][anchor_col] = PIECE_CHAR
    return self
  
  # Takes coordinate and ship size, returns list of possible swing coordinates
  def get_allowed_swing_points(self, anchor_row: str, anchor_col: int, ship_size: int) -> tuple[str]:
    possible_positions = []
    swing_down_allowed = True
    swing_right_allowed = True 
    swing_up_allowed = True
    swing_left_allowed = True
    # The offset of 1 accounts for only needing to be ship_size-1 spots away from the anchor
    right_swing_point = anchor_col+ship_size-1
    down_swing_point = STR_TO_INT[anchor_row]+ship_size-1
    left_swing_point = anchor_col-ship_size+1
    up_swing_point = STR_TO_INT[anchor_row]-ship_size+1
    
    # If down swing is in the grid
    if (down_swing_point <= 9): 
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(STR_TO_INT[anchor_row]+1, down_swing_point-1): # Don't want to count anchor as a different ship
        if (self.state[n][anchor_col] != '~'):
          swing_down_allowed = False
    else: 
      swing_down_allowed = False

    # If right swing is in the grid
    if (right_swing_point <= 9):
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(anchor_col+1, right_swing_point-1):
        if (self.state[STR_TO_INT[anchor_row]][n] != '~'):
          swing_right_allowed = False
    else: 
      swing_right_allowed = False

    # If up swing is in the grid
    if (up_swing_point >= 0): 
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(up_swing_point, STR_TO_INT[anchor_row]):
        if (self.state[n][anchor_col] != '~'):
          swing_up_allowed = False
    else: 
      swing_up_allowed = False

    # If left swing is in the grid
    if (left_swing_point >= 0): 
      # If a coordinate in the candidate ship space is taken, the swing is not allowed
      for n in range(left_swing_point, anchor_col):
        if (self.state[STR_TO_INT[anchor_row]][n] != '~'):
          swing_left_allowed = False
    else: 
      swing_left_allowed = False

    if (swing_down_allowed): possible_positions.append(INT_TO_STR[down_swing_point] + str(anchor_col))
    if (swing_right_allowed): possible_positions.append(anchor_row + str(right_swing_point))
    if (swing_up_allowed): possible_positions.append(INT_TO_STR[up_swing_point] + str(anchor_col))
    if (swing_left_allowed): possible_positions.append(anchor_row + str(left_swing_point))
    return possible_positions

  # Place down a single ship
  def place_ship(self, ship: str):
    anchor_point = None # String ex. "A1"
    swing_point = None # String ex. "A1"
    # Place anchor point
    while(anchor_point == None):
      print(self)
      print("Choose an anchor point (ex. A1) for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
      player_choice = input("Enter your choice here: ")
      # Check input length
      if (len(player_choice) != 2): continue
      # Check input validity
      # TO-DO: make lowercase char value as coordinate work
      anchor_coordinate_info = coordinate_to_tuple(player_choice)
      if (coordinate_in_board(anchor_coordinate_info[0], anchor_coordinate_info[1])):
        anchor_point = player_choice

    # Place the anchor point on the board and show it to the player
    self.place_anchor(anchor_coordinate_info[0], anchor_coordinate_info[1])
    # TO-DO: show the possible secondary points on the board using ?'s
    print(self)

    # Get possible secondary points
    allowed_swing_points = self.get_allowed_swing_points(anchor_coordinate_info[0], anchor_coordinate_info[1], SHIPS_SIZES[ship])
    while (swing_point == None):
      print("Choose a second point for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
      # TO-DO: make it possible to reset the anchor (maybe 00 -> reset anchor)
      print("The options are: " + " ".join(allowed_swing_points))
      player_choice = input("Enter your choice here: ")
      # TO-DO: make sure ships have no overlap
      if (player_choice in allowed_swing_points):
        swing_point = player_choice
    
    # Place ship onto board
    swing_coordinate_info = coordinate_to_tuple(player_choice)
    # Anchor and swing x & y aliases, all in integer form
    a_x, a_y = (STR_TO_INT[anchor_coordinate_info[0]], anchor_coordinate_info[1])
    s_x, s_y = (STR_TO_INT[swing_coordinate_info[0]], swing_coordinate_info[1])
    if a_y == s_y:  # Horizontal orientation
      for x in range(min(a_x, s_x), max(a_x, s_x)+1):
        self.state[x][a_y] = PIECE_CHAR
    if a_x == s_x:  # Vertical orientation
      for y in range(min(a_y, s_y), max(a_y, s_y)+1):
        self.state[a_x][y] = PIECE_CHAR
      
    print(self)

  # Add labels to the board representation
  def __str__(self):
    col_titles = [' '] + [str(i) for i in range(GRID_SIZE)]
    row_titles = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    return " ".join(col_titles) + "\n" + "\n".join([row_titles[i] + " " + " ".join(self.state[i]) for i in range(GRID_SIZE)])

def main():
  player_grid = BoardState()
  player_grid.place_ship(SHIPS_NAMES[0])
  player_grid.place_ship(SHIPS_NAMES[1])

if __name__ == "__main__":
  main()