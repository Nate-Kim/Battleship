GRID_SIZE = 10
SHIPS_SIZES = {"aircraft carrier": 5, 
              "battleship": 4, 
              "cruiser": 3, 
              "submarine": 3, 
              "destroyer": 2}
SHIPS_NAMES = ["aircraft carrier", "battleship", "cruiser", "submarine", "destroyer"]
MIRRORED_BOARD_LABELS = True
STR_TO_INT = {"A":0,"B":1,"C":2,"D":3,"E":4,"F":5,"G":6,"H":7,"I":8,"J":9}
INT_TO_STR = {0:"A",1:"B",2:"C",3:"D",4:"E",5:"F",6:"G",7:"H",8:"I",9:"J"}


def initialize_board():
  # 1-10 at the top of the board
  col_titles = [' '] + [str(i) for i in range(GRID_SIZE)]
  # A-J along the side of the board
  row_titles = ['A','B','C','D','E','F','G','H','I','J']

  board = [col_titles] + [[row] + ['~'] * GRID_SIZE for row in row_titles]
  return board

# Takes a coordinate and ensures it lies in board range
def validate_placement(c: str, i: int) -> bool:
  # Checks that the entry is within the grid
  if (i in range(10) and STR_TO_INT[c] in range(10)): 
    return True
  return False

# Takes coordinate and ship size, returns list of possible swing coordinates
def get_allowed_swing_points(c: str, i: int, ship_size: int) -> list[str]:
  possible_positions = []
  # The offset of 2 accounts for only needing to be ship_size-1 spots away from the anchor
  # If right swing is possible, append the right swing coordinate
  if (i+ship_size-1 <= 9): possible_positions.append(c + str(i+ship_size-1))
  # If down swing is possible, append the down swing coordinate
  if (STR_TO_INT[c]+ship_size-1 <= 9): possible_positions.append(INT_TO_STR[STR_TO_INT[c]+ship_size-1] + str(i))
  # If left swing is possible, append the left swing coordinate
  if (i-ship_size+1 >= 0): possible_positions.append(c + str(i-ship_size+1))
  # If up swing is possible, append the up swing coordinate
  if (STR_TO_INT[c]-ship_size+1 >= 0): possible_positions.append(INT_TO_STR[STR_TO_INT[c]-ship_size+1] + str(i))
  return possible_positions

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
  def __init__(self, state=initialize_board()):
    self.state = state

  def place_anchor(self: "BoardState", c: str, i: int) -> "BoardState":
    row_choice = STR_TO_INT[c]
    self.state[row_choice+1][i+1] = '+'
    return self

  def place_ship(self):
    anchor_point = None # String ex. "A1"
    swing_point = None # String ex. "A1"
    num_ships_placed = 0
    for ship in SHIPS_NAMES:
      # Place anchor point
      while(anchor_point == None):
        print(self)
        print("Choose an anchor point (ex. A1) for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
        player_choice = input("Enter your choice here: ")
        # Check input length
        if (len(player_choice) != 2): continue
        # Check input validity
        coordinate_info = coordinate_to_tuple(player_choice)
        if (validate_placement(coordinate_info[0], coordinate_info[1])):
          anchor_point = player_choice
          num_ships_placed += 1
      # Place the anchor point on the board and show it to the player
      self.place_anchor(coordinate_info[0], coordinate_info[1])
      print(self)
      # Get possible secondary points
      allowed_swing_points = get_allowed_swing_points(coordinate_info[0], coordinate_info[1], SHIPS_SIZES[ship])
      while (swing_point == None):
        print("Choose a second point for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
        # Should make it possible to reset the anchor
        print("The options are: " + " ".join(allowed_swing_points))
        player_choice = input("Enter your choice here: ")
        if (len(player_choice) == 2 and validate_placement(player_choice[0], player_choice[1])):
          break
          possiblePositions = 1
          anchor_point = player_choice
          num_ships_placed += 1



  def __str__(self):
    return "\n".join(" ".join(map(str, row)) for row in self.state)

  def __repr__(self) -> str:
    return self.__str__()

  def __eq__(self, other):
    if isinstance(other, BoardState):
      return self.state == other.state
    return False

  def __hash__(self):
    return hash(tuple(map(tuple, self.state)))

def main():
  player_grid = BoardState()
  player_grid.place_ship()
  print(player_grid)

if __name__ == "__main__":
  main()