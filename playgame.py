import random
import os
import copy

import numpy as np
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Conv2D, Flatten, Dense, Reshape, Input # type: ignore
from tensorflow.keras.initializers import HeNormal # type: ignore
from tensorflow.keras.regularizers import l2 # type: ignore
import matplotlib.pyplot as plt
import pickle

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
NREPS = 10 # Number of times an algorithm tests on a sample board if testing is selected

H_NREPS = 5000 # Number of sims for get_heatmap (more = more accurate heatmap). Used in heatmap & NN moves.
NN_NREPS = 300 # Number of new samples for NN training and validation
GENERATE_DATA = False  # Generate more samples for NN training and validation
EPOCHS = 200 # Number of epochs for neural network

"""GLOBAL VARIABLES FOR HUMAN AI"""
rowNum = 0
colNum = 0
targetStack = []
hitMarkers = []
targetMode = False
destroyMode = False
clearHitMarkers = False
humanSimSunkResult = ""
probableHuman = False #boolean variable. True is to do probability strat and false is to do even strat
removeFromStackCount = int
isAppended = False

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

# MCTS Implementation
class mcts:
  def __init__(self, env, samples):
    self.env = env
    self.move_sim = samples
    self.priority = 5
    self.max_attempts = 100  # Maximum number of attempts to place a ship

  def monte_carlo(self, fog_of_war):
    simulations = []
    for _ in range(self.move_sim):
      simulated_board, intersect = self.simulate_ship(fog_of_war)
      if intersect:
        for _ in range(self.priority):
          simulations.append(simulated_board)
      simulations.append(simulated_board)
    simulations = np.array(simulations)
    percentages = np.mean(simulations, axis=0)
    return percentages

  def simulate_ship(self, fog_of_war):
    simulated_board = np.zeros((GRID_SIZE, GRID_SIZE))
    intersect = 0
    for ship_name, ship_size in SHIPS_SIZES.items():
      placed = False
      attempts = 0
      while not placed and attempts < self.max_attempts:
        attempts += 1
        orientation = random.choice(['H', 'V'])
        if orientation == 'H':
          row = random.randint(0, GRID_SIZE - 1)
          col = random.randint(0, GRID_SIZE - ship_size)
          if all(fog_of_war[row][c] == '~' for c in range(col, col + ship_size)):
            for c in range(col, col + ship_size):
              simulated_board[row][c] = 1
              if fog_of_war[row][c] == 'X':
                intersect += 1
            placed = True
          else:
            row = random.randint(0, GRID_SIZE - ship_size)
            col = random.randint(0, GRID_SIZE - 1)
            if all(fog_of_war[r][col] == '~' for r in range(row, row + ship_size)):
              for r in range(row, row + ship_size):
                simulated_board[r][col] = 1
                if fog_of_war[r][col] == 'X':
                  intersect += 1
              placed = True
    return simulated_board, intersect

  def ai_mcts_move(self):
    fog_of_war = self.env.fog_of_war
    #print("Fog of War:", fog_of_war)
    percentages = self.monte_carlo(fog_of_war)
    #print("Probabilities:", percentages)
    max_prob = -1
    move = (0, 0)

    if self.env.target_mode and self.env.hit_stack:
      move = self.env.hit_stack.pop()
      #print("Target mode. Move from hit stack:", move)
    else:
      for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
          if self.env.state[row][col] not in ('X', 'O') and percentages[row][col] > max_prob:
            max_prob = percentages[row][col]
            move = (row, col)
      #print("Selected move based on probabilities:", move)

    row, col = move
    if self.env.state[row][col] == '#':
      self.env.fog_of_war[row][col] = 'X'
      self.env.state[row][col] = 'X'
      self.env.target_mode = True
      self.env.update_probabilities_after_hit(row, col)
      self.update_hit_stack(row, col)
      #print("Hit at:", move)
      sunk_ship = self.env.check_ship_sunk()
      if sunk_ship:
        self.env.hit_stack = []
        self.env.target_mode = False
        #print(f"The enemy has sunk your {sunk_ship}!")
      return True
    else:
      self.env.fog_of_war[row][col] = 'O'
      self.env.state[row][col] = 'O'
      #print("Miss at:", move)
      self.handle_miss(row, col)
      return False

  def update_hit_stack(self, row, col):
    directions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    for dr, dc in directions:
      nr, nc = row + dr, col + dc
      if self.env.is_in_bounds(nr, nc) and self.env.state[nr][nc] not in ('X', 'O'):
        self.env.hit_stack.append((nr, nc))
    #print("Updated hit stack:", self.env.hit_stack)

  def handle_miss(self, row, col):
    hit_sequences = self.get_hit_sequences()
    for seq in hit_sequences:
      if len(seq) >= 3:
        r1, c1 = seq[0]
        r2, c2 = seq[-1]
        if (r1 == r2 and col in range(min(c1, c2), max(c1, c2) + 1)) or (c1 == c2 and row in range(min(r1, r2), max(r1, r2) + 1)):
          if r1 == r2:  # Horizontal sequence
            if c1 > 0 and self.env.state[r1][c1 - 1] not in ('X', 'O'):
              self.env.hit_stack.append((r1, c1 - 1))
            if c2 < GRID_SIZE - 1 and self.env.state[r1][c2 + 1] not in ('X', 'O'):
              self.env.hit_stack.append((r1, c2 + 1))
          elif c1 == c2:  # Vertical sequence
            if r1 > 0 and self.env.state[r1 - 1][c1] not in ('X', 'O'):
              self.env.hit_stack.append((r1 - 1, c1))
            if r2 < GRID_SIZE - 1 and self.env.state[r2 + 1][c1] not in ('X', 'O'):
              self.env.hit_stack.append((r2 + 1, c1))
    #print("Updated hit stack after miss:", self.env.hit_stack)

  def get_hit_sequences(self):
    hits = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if self.env.state[r][c] == 'X']
    sequences = []
    for hit in hits:
      r, c = hit
      # Check horizontal sequence
      horiz_seq = [(r, c)]
      for dc in range(1, GRID_SIZE - c):
        if self.env.state[r][c + dc] == 'X':
          horiz_seq.append((r, c + dc))
        else:
          break
      if len(horiz_seq) > 1:
        sequences.append(horiz_seq)
      # Check vertical sequence
      vert_seq = [(r, c)]
      for dr in range(1, GRID_SIZE - r):
        if self.env.state[r + dr][c] == 'X':
          vert_seq.append((r + dr, c))
        else:
          break
      if len(vert_seq) > 1:
        sequences.append(vert_seq)
    return sequences

# Holds all information about a player's board
class BoardState:
  # state represents a player's view of their own board
  # fog_of_war represents a player's view of their opponent's board
  # ships will be an array of arrays, each array holding the grid locations of each segment of each ship
  #  this is to determine when one player destroys one of their opponent's ships
  # ships_dict will have a ship name key to access the grid locations of the key ship
  #  this is to know the name of the ship that is destroyed so that the name can be
  # ships_remaining will contain the names of ships that have yet to be sunk
  # locations_destroyed is an array of ship location arrays that hold grid location arrays as ints
  # searching tells the NN whether to use heatmap or probability grid, set in transform_data
  def __init__(self, state=None, fog_of_war=None, ships=None, ships_dict=None, 
               ships_remaining=None, locations_destroyed=None, samples=100, searching=None, network=None):
    self.state = state if state is not None else [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.fog_of_war = fog_of_war if fog_of_war is not None else [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.ships = ships if ships is not None else []
    self.ships_dict = {} if ships_dict is None else {k: v[:] for k, v in ships_dict.items()}
    self.ships_remaining = list(SHIPS_NAMES) if ships_remaining is None else list(ships_remaining)
    self.locations_destroyed = [] if locations_destroyed is None else list(locations_destroyed)
    self.searching = True if searching is None else searching
    self.network = network

    self.probability_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.hit_stack = []
    self.target_mode = False
    self.random_mode = True
    self.samples = samples
    self.mcts = mcts(self, samples)

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
    if (left_swing_point >= 0): swing_left_allowed = all(self.state[anchor_row][n] == '~' for n in range(left_swing_point, anchor_col))

    # Append swing locations depending on if they are allowed
    if (swing_down_allowed): possible_positions.append(INT_TO_STR[down_swing_point] + str(anchor_col))
    if (swing_right_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(right_swing_point))
    if (swing_up_allowed): possible_positions.append(INT_TO_STR[up_swing_point] + str(anchor_col))
    if (swing_left_allowed): possible_positions.append(INT_TO_STR[anchor_row] + str(left_swing_point))

    return possible_positions
  # Prompt user to enter an anchor point for ship placement, returns tuple of grid coordinates
  #  Example return: (2,4)
  def get_anchor_point(self, ship: str) -> tuple[int, int]:
    # Place anchor point
    while True:
      # Print statements
      clear_console()
      self.print_grid(fog_of_war=False)
      print("Choose an anchor point (ex. A1) for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
      player_choice = input("Enter your choice here: ")
      # Check input
      input_coordinate = input_to_coordinate(player_choice)
      # If bad input, reset the choosing process
      if input_coordinate != (-1,-1) and self.state[input_coordinate[0]][input_coordinate[1]] == '~':
        return input_coordinate
  # Prompt user to enter a swing point for ship orientation, returns tuple of grid coordinates
  #  Example return: (5,1)
  def get_swing_point(self, ship: str, valid_swing_points) -> tuple[int, int]:
    while True:
      # Print statements
      clear_console()
      self.print_grid(fog_of_war=False)
      print("Choose a second point for your " + ship + ", which has size " + str(SHIPS_SIZES[ship]) + ".")
      print("The options are: " + " ".join(valid_swing_points))
      player_choice = input("Enter your choice here: ")
      # Check input
      input_coordinate = input_to_coordinate(player_choice)
      # If bad input, reset the choosing process
      if input_coordinate != (-1,-1) and (INT_TO_STR[input_coordinate[0]] + str(input_coordinate[1]) in valid_swing_points):
        return input_coordinate

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
      while True:
        random_row = random.randint(0, GRID_SIZE - 1)
        random_col = random.randint(0, GRID_SIZE - 1)
        if self.state[random_row][random_col] != '#':
          # Found a coordinate not on top of a ship
          anchor_row, anchor_col = random_row, random_col
          break
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
        self.locations_destroyed.append(ship_locations)
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
  # Reset the board (for testing AI efficiency)
  def reset(self) -> None:
    global rowNum
    global colNum
    global targetStack
    global targetMode
    global destroyMode
    global humanSimSunkResult
    global hitMarkers
    global clearHitMarkers
    global isAppended
    self.state = [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.fog_of_war = [['~'] * GRID_SIZE for _ in range(GRID_SIZE)]
    self.ships = []
    self.ships_dict = {}
    self.ships_remaining = list(SHIPS_NAMES)
    self.locations_destroyed = []
    rowNum = 0
    colNum = 0
    targetStack = []
    hitMarkers = []
    targetMode = False
    destroyMode = False
    clearHitMarkers = False
    humanSimSunkResult = ""
    isAppended = False
    #reset global variables

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
  def human_sim_move(self) -> bool:
    #POTENTIAL IMPROVEMENT FOR LATER: Currently, target mode checks right, left, down, and then up.
    #It is more efficient to check either vertical after checking right.
    #This is because hitting in a checkerboard pattern goes left to right in our implementation and the chance that 
    #a ship size smaller than 3 is on the left of the hit tile after hitting right is smaller than the chance of it being a vertical ship
    #if we implemented the checkerboard pattern to iterate up down the problem would be the opposite.
    global rowNum
    global colNum
    global targetMode
    global destroyMode
    global targetStack
    global hitMarkers
    global clearHitMarkers
    global humanSimSunkResult
    global probableHuman
    global removeFromStackCount
    global isAppended

    # print("target stack")
    # print(targetStack)
    #disables destroying of ships and clears the stack of tiles to hit if the ship is destroyed statement comes up
    if (humanSimSunkResult != ""):
      if(destroyMode and len(targetStack) != 0 and isAppended):
        targetStack.pop() #popping to ge rid of the choice the destroy mode added last call of human_sim_move
      #latestDirection = hitMarkers[len(hitMarkers) -1][2]
      destroyMode = False
      shipSunkList = self.locations_destroyed[len(self.locations_destroyed) - 1]
      # print("destroyed ship coords")
      # print(shipSunkList)
      # print("hit markers")
      # print(hitMarkers)
      #since a ship was destroyed, remove all hit markers releated to that destroyed ship
      listTemp = []
      for x in hitMarkers:
        if(not([x[0], x[1]] in shipSunkList)):
          listTemp.append(x)
          #print("keep " + str(x))
        # else:
          #print("remove " + str(x))
      hitMarkers = listTemp
      # print("hitmarkers afterwards")
      # print(hitMarkers)
      #i = len(hitMarkers) -1
      #while(i >= 0):
        #if(hitMarkers[i][2] == latestDirection):
          #hitMarkers.pop()
        #else:
          #break
        #i -= 1
      #hitMarkers.pop() #removing the hitmarker that acts as the pivot point between the two cardinal directions
      
      
      if(len(hitMarkers) == 0): # only clear when there are no more hitmarkers to investigate
        targetStack = [] #clear list
        #go back to searching we used all the info we had on the destroyed ships
        clearHitMarkers = False
        destroyMode = False
        targetMode = False
      else:
        clearHitMarkers = True
        self.check_hit_markers()
      humanSimSunkResult = ""
      # print("target stack afterwards")
      # print(targetStack)
    #enabled if the algorithm hits any ship part
    #adds adjacent tiles to the stack to iterate through
    if (targetMode):
      #print("targetMode")
      isBlocked = False
      move = targetStack.pop()
      if self.state[move[0]][move[1]] not in ('X', 'O'):
        if self.state[move[0]][move[1]] == '#':
          self.fog_of_war[move[0]][move[1]] = 'X'
          self.state[move[0]][move[1]] = 'X'
          hitMarkers.append(move)
          if (move[2] == "up"):
            if (move[0] - 1 >= 0 and self.state[move[0] - 1][move[1]] not in ('X', 'O')):
              targetStack.append((move[0] - 1, move[1], "up"))
            else:
              isBlocked = True
          elif (move[2] == "down"):
            if (move[0] + 1 <= 9 and self.state[move[0] + 1][move[1]] not in ('X', 'O')):
              targetStack.append((move[0] + 1, move[1], "down"))
            else:
              isBlocked = True
          elif (move[2] == "left"):
            if (move[1] - 1 >= 0 and self.state[move[0]][move[1] - 1] not in ('X', 'O')):
              targetStack.append((move[0], move[1] - 1, "left"))
            else:
              isBlocked = True
          else:  # right
            if (move[1] + 1 <= 9 and self.state[move[0]][move[1] + 1] not in ('X', 'O')):
              targetStack.append((move[0], move[1] + 1, "right"))
            else:
              isBlocked = True
          if(isBlocked):
            targetMode = False
            clearHitMarkers = True
            self.check_hit_markers()
          else:
            targetMode = False # turns off target mode and enable destroy mode to pop the stack and destroy ship
            destroyMode = True
          return True
        else:  # is ~
          self.fog_of_war[move[0]][move[1]] = 'O'
          self.state[move[0]][move[1]] = 'O'
          return False
    elif (destroyMode):
      #print("destroyMode")
      while(True):
        isAppended = False
        move = targetStack.pop() #grabs latest tile and hits
        if self.state[move[0]][move[1]] not in ('O'):
          if (move[2] == "up"):
            if (move[0] - 1 >= 0 and self.state[move[0] - 1][move[1]] not in ('O', 'X')):
              targetStack.append((move[0] - 1, move[1], "up"))
              isAppended = True
          elif (move[2] == "down"):
            if (move[0] + 1 <= 9 and self.state[move[0] + 1][move[1]] not in ('O', 'X')):
              targetStack.append((move[0] + 1, move[1], "down"))
              isAppended = True
          elif (move[2] == "left"):
            if (move[1] - 1 >= 0 and self.state[move[0]][move[1] - 1] not in ('O', 'X')):
              targetStack.append((move[0], move[1] - 1, "left"))
              isAppended = True
          else:  # right
            if (move[1] + 1 <= 9 and self.state[move[0]][move[1] + 1] not in ('O', 'X')):
              targetStack.append((move[0], move[1] + 1, "right"))
              isAppended = True
          if self.state[move[0]][move[1]] not in ('X'):
            if self.state[move[0]][move[1]] == '#':
              self.fog_of_war[move[0]][move[1]] = 'X'
              self.state[move[0]][move[1]] = 'X'
              hitMarkers.append(move)
              return True
            else:  # miss
              self.fog_of_war[move[0]][move[1]] = 'O'
              self.state[move[0]][move[1]] = 'O'
              if(isAppended):
                #algorithm was certain it can destroy a ship in this particular cardinal direction. So this must mean the algorithm has hit multiple ships lined up together 
                # remove latest append since we have discovered the current move is a miss 
                targetStack.pop() 
              else: # ELSE BODY IS A NEW ADDITION
                clearHitMarkers=True
                self.check_hit_markers()
              destroyMode = False
              clearHitMarkers = True
              self.check_hit_markers()
              return False
    elif(clearHitMarkers):
      #print("clearHitMarkers")
      #behave similar to target mode: pop decisions until a hit is found. Then destroy that ship with destroy mode
      move = targetStack.pop()
      isAppended = False
      #if(removeFromStackCount != 0):
        #removeFromStackCount -= 1
      while(self.state[move[0]][move[1]] in ('O', 'X')):
        move = targetStack.pop()
      if(self.state[move[0]][move[1]] == '#'):
        self.fog_of_war[move[0]][move[1]] = 'X'
        self.state[move[0]][move[1]] = 'X'
        hitMarkers.append(move)
        #for i in range(removeFromStackCount):
          #targetStack.pop()
        if(move[2] == "up" and move[0] - 1 >= 0 and self.fog_of_war[move[0] - 1][move[1]] == "~"):
          #if(self.fog_of_war[move[0] + 1][move[1]] == '~' and move[0] + 1 <=9):
            #targetStack.append((move[0] + 1, move[1], "down"))
          targetStack.append((move[0] - 1, move[1], "up"))
          isAppended = True
        elif(move[2] == "down" and move[0] + 1 <= 9 and self.fog_of_war[move[0] + 1][move[1]] == "~"):
          #if(self.fog_of_war[move[0] - 1][move[1]] == '~' and move[0] - 1 >= 0):
            #targetStack.append((move[0] - 1, move[1], "up"))
          targetStack.append((move[0] + 1, move[1], "down"))
          isAppended = True
        elif(move[2] == "left" and move[1] - 1 >= 0 and self.fog_of_war[move[0]][move[1] - 1] == "~"):
          #if(self.fog_of_war[move[0]][move[1] + 1] == '~' and move[1] + 1 <= 9):
            #targetStack.append((move[0], move[1] + 1, "right"))
          targetStack.append((move[0], move[1] - 1, "left"))
          isAppended = True
        elif(move[2] == "right" and move[1] + 1 <= 9 and self.fog_of_war[move[0]][move[1] + 1] == "~"): #right
          #if(self.fog_of_war[move[0]][move[1] - 1] == '~' and move[1] - 1 >= 0):
            #targetStack.append((move[0], move[1] - 1, "left"))
          targetStack.append((move[0], move[1] + 1, "right"))
          isAppended = True
        clearHitMarkers = False
        destroyMode = True
        #loop gets rid of choices added by set up target mode during clear hit marker stage since we don't need to consider the other options we haven't popped yet

        return True
      #is ~
      self.fog_of_war[move[0]][move[1]] = 'O'
      self.state[move[0]][move[1]] = 'O'
      return False

    else: #this is the search pattern. Hits tiles in a checkerboard style
      #print("search")
      if probableHuman:
        decision = self.get_max_probability()
        if self.state[decision[0]][decision[1]] == '#':
          self.fog_of_war[decision[0]][decision[1]] = 'X'
          self.state[decision[0]][decision[1]] = 'X'
          hitMarkers.append((decision[0], decision[1], "start"))
          targetMode = True
          self.set_up_target_mode(decision[0], decision[1])
          return True
        if self.state[decision[0]][decision[1]] == '~':
          self.fog_of_war[decision[0]][decision[1]] = 'O'
          self.state[decision[0]][decision[1]] = 'O'
          return False   
      else:
        while(True):
          if self.state[rowNum][colNum] not in ('X', 'O'):
            if self.state[rowNum][colNum] == '#':
              self.fog_of_war[rowNum][colNum] = 'X'
              self.state[rowNum][colNum] = 'X'
              targetMode = True
              hitMarkers.append((rowNum, colNum, "start"))
              self.set_up_target_mode(rowNum, colNum)
              return True
            if self.state[rowNum][colNum] == '~':
              self.fog_of_war[rowNum][colNum] = 'O'
              self.state[rowNum][colNum] = 'O'
              self.next_tile()
              return False
        
          self.next_tile()

      if self.target_mode and self.hit_stack:
          move = self.hit_stack.pop()
      else:
          self.target_mode = False
          while True:
              move = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
              if self.state[move[0]][move[1]] not in ('X', 'O'):
                  break

      row, col = move

      if self.state[row][col] == '#':
          self.fog_of_war[row][col] = 'X'
          self.state[row][col] = 'X'
          self.target_mode = True

          if row > 0 and self.state[row - 1][col] not in ('X', 'O'):
              self.hit_stack.append((row - 1, col))
          if row < GRID_SIZE - 1 and self.state[row + 1][col] not in ('X', 'O'):
              self.hit_stack.append((row + 1, col))
          if col > 0 and self.state[row][col - 1] not in ('X', 'O'):
              self.hit_stack.append((row, col - 1))
          if col < GRID_SIZE - 1 and self.state[row][col + 1] not in ('X', 'O'):
              self.hit_stack.append((row, col + 1))

          return True
      else:
          self.fog_of_war[row][col] = 'O'
          self.state[row][col] = 'O'
          return False
  # Chooses a move based on Monte Carlo Simulation
  #  returns a boolean, True for ship hit or False for ship not hit
  def AI_mcts_move(self) -> bool:
    return self.mcts.ai_mcts_move()
  # Chooses a move based on neural network strategy
  #  returns a boolean, True for ship hit or False for ship not hit
  def neural_network_move(self) -> bool:
    """
    IDs for input:
      0: unexplored (0th layer for 3D one-hot representation)
      1: hit and destroyed OR miss (1st layer for 3D one-hot representation)
      2: hit but not destroyed (2nd layer for 3D one-hot representation)
      3: ship simulated
      4: ship simulated on top of undestroyed ship
    Rules:
      - Input board with 0's, 1's, 2's
      - Can make a move on 0
      - Ideally should target locations near existing 2's
      - The generated data 
    """
    if self.network == None:
      self.train_neural_network()
    
    network = self.network

    # input state
    transformed_state = self.transform_data()
    test_tensor = np.zeros((10, 10, 3))
    for row in range(GRID_SIZE):
      for col in range(GRID_SIZE):
        if transformed_state[row][col] == 0:
          test_tensor[row][col][0] = 1
        if transformed_state[row][col] == 1:
          test_tensor[row][col][1] = 1
        if transformed_state[row][col] == 2:
          test_tensor[row][col][2] = 1
    if self.searching: test_value = self.get_probability_grid()
    else: test_value = self.get_heatmap(nreps=H_NREPS, current_state=self.transform_data())    

    # Normalize test value element magnitudes
    test_value /= np.max(test_value)

    test_data = np.expand_dims(test_tensor, axis=0)
    test_label = np.expand_dims(test_value, axis=0)

    loss, accuracy = network.evaluate(test_data, test_label, verbose=0)
    nn_probability_array = np.squeeze(network.predict(test_data, verbose=0))

    for row in range(GRID_SIZE):
      for col in range(GRID_SIZE):
        if test_value[row][col] == 0: 
          nn_probability_array[row][col] = 0

    nn_probability_array /= np.max(nn_probability_array) 
    max_index = np.argmax(nn_probability_array)
    max_row, max_col = np.unravel_index(max_index, nn_probability_array.shape)
    comparisons = False
    if comparisons:
      corresponding_in_pgrid = test_value[max_row][max_col]
      flattened_array = np.array(test_value).flatten()
      sorted_array = np.sort(flattened_array)[::-1]
      for i in range(len(sorted_array)):
        if sorted_array[i] == corresponding_in_pgrid:
          print("Next move:")
          print(f"Max Location: ({max_row}, {max_col})")
          print(f"That is the {i} best move.")
          break

    stats = False
    if stats:
      print(f"Loss: {loss}")
      print(f"Root mean squared error: {accuracy}")
      print(nn_probability_array)
      print(f"Max Location: ({max_row}, {max_col})")

    if self.state[max_row][max_col] == '#':        
      self.fog_of_war[max_row][max_col] = 'X'
      self.state[max_row][max_col] = 'X'
      return True
    if self.state[max_row][max_col] == '~':
      self.fog_of_war[max_row][max_col] = 'O'
      self.state[max_row][max_col] = 'O'
      return False
  # Chooses a move based on heatmap strategy
  #  returns a boolean, True for ship hit or False for ship not hit
  def heatmap_move(self) -> bool:
    # prob. grid has 0-1 values, get_heatmap has absolute values
    if self.searching: heatmap = np.array(self.get_probability_grid())
    else: heatmap = np.array(self.get_heatmap(nreps=H_NREPS, current_state=self.transform_data()))
    

    max_index = np.argmax(heatmap)
    max_row, max_col = np.unravel_index(max_index, heatmap.shape)

    if self.state[max_row][max_col] == '#':        
      self.fog_of_war[max_row][max_col] = 'X'
      self.state[max_row][max_col] = 'X'
      self.searching = False
      return True
    if self.state[max_row][max_col] == '~':
      self.fog_of_war[max_row][max_col] = 'O'
      self.state[max_row][max_col] = 'O'
      return False


  """MOVE HELPERS"""
  # Generates all possible positions of all remaining ships and hits position with highest of existence
  #  returns a the grid location with highest probability of a ship being there
  # only works when in search mode
  def get_max_probability(self) -> tuple[int, int]:
    # Probabilities of each position start as all 0
    probability_array = np.zeros((10, 10))

    # Loop through every remaining ship name
    for ship_name in self.ships_remaining:
      # Get the current ship size
      current_ship_size = SHIPS_SIZES[ship_name]
      # Record right swing position and down swing position from current grid point
      # For each grid location in the grid
      for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
          # If a right swing is possible check the right swing orientation placement feasibility
          if col <= GRID_SIZE-current_ship_size:
            # If all of the grid locations in the current possible position are unchecked, add to probability grid
            if all(self.fog_of_war[row][col+n] == '~' for n in range(current_ship_size)):
              for i in range(current_ship_size):
                probability_array[row][col+i] = probability_array[row][col+i] + 1
          # If a down swing is possible check the down swing orientation placement feasibility
          if row <= GRID_SIZE-current_ship_size:
          # If all of the grid locations in the current possible position are unchecked, add to probability grid
            if all(self.fog_of_war[row+n][col] == '~' for n in range(current_ship_size)):
              for i in range(current_ship_size):
                probability_array[row+i][col] = probability_array[row+i][col] + 1
    
    max_index = np.argmax(probability_array)
    max_row, max_col = np.unravel_index(max_index, probability_array.shape)

    return (max_row, max_col)
  def get_probability_grid(self):
    # Probabilities of each position start as all 0
    probability_array = np.zeros((10, 10))

    # Loop through every remaining ship name
    for ship_name in self.ships_remaining:
      # Get the current ship size
      current_ship_size = SHIPS_SIZES[ship_name]
      # Record right swing position and down swing position from current grid point
      # For each grid location in the grid
      for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
          # If a right swing is possible check the right swing orientation placement feasibility
          if col <= GRID_SIZE-current_ship_size:
            # If all of the grid locations in the current possible position are unchecked, add to probability grid
            if all(self.fog_of_war[row][col+n] == '~' for n in range(current_ship_size)):
              for i in range(current_ship_size):
                probability_array[row][col+i] = probability_array[row][col+i] + 1
          # If a down swing is possible check the down swing orientation placement feasibility
          if row <= GRID_SIZE-current_ship_size:
          # If all of the grid locations in the current possible position are unchecked, add to probability grid
            if all(self.fog_of_war[row+n][col] == '~' for n in range(current_ship_size)):
              for i in range(current_ship_size):
                probability_array[row+i][col] = probability_array[row+i][col] + 1
    
    max_value = np.max(probability_array)
    probability_array /= max_value

    return probability_array
  # Human sim helpers
  def next_tile(self) -> None:
    global colNum
    global rowNum

    colNum += 2
    if colNum > 9:
      rowNum += 1
      if rowNum % 2 == 0:
        colNum = 0
      else:
        colNum = 1
  def next_tile_r(self) -> None:
    global colNum
    global rowNum

    colNum -= 2
    if colNum < 0:
      rowNum -= 1
      if rowNum % 2 == 1:
        colNum = 9
      else:
        colNum = 8
  def set_up_target_mode(self, rowNum, colNum) -> int:
    global targetStack
    count = 0
    # above tile
    if (rowNum - 1 >= 0 and self.state[rowNum - 1][colNum] not in ('X', 'O')):
      targetStack.append((rowNum - 1, colNum, "up"))
      count += 1
    # below tile
    if (rowNum + 1 <= 9 and self.state[rowNum + 1][colNum] not in ('X', 'O')):
      targetStack.append((rowNum + 1, colNum, "down"))
      count += 1
    # left tile
    if (colNum - 1 >= 0 and self.state[rowNum][colNum - 1] not in ('X', 'O')):
      targetStack.append((rowNum, colNum - 1, "left"))
      count += 1
    # right tile
    if (colNum + 1 <= 9 and self.state[rowNum][colNum + 1] not in ('X', 'O')):
      targetStack.append((rowNum, colNum + 1, "right"))
      count += 1
    return count # count is only for knowing how many choices to remove during clear hit marker stage
  def check_hit_markers(self):
    global hitMarkers
    #marker = hitMarkers.pop()
    i = 1
    while(i <= len(hitMarkers)):
      marker = hitMarkers[len(hitMarkers) - i]
      if(marker[2] != "start"):
        result = self.set_up_target_mode(marker[0], marker[1])
        if(result != 0):
          break
      else:
        break
      i += 1
  # Monte Carlo Sim helpers
  def update_probabilities_after_hit(self, row: int, col: int) -> None:
    if row > 0 and self.state[row - 1][col] not in ('X', 'O'):
      self.probability_grid[row - 1][col] += 10
    if row < GRID_SIZE - 1 and self.state[row + 1][col] not in ('X', 'O'):
      self.probability_grid[row + 1][col] += 10
    if col > 0 and self.state[row][col - 1] not in ('X', 'O'):
      self.probability_grid[row][col - 1] += 10
    if col < GRID_SIZE - 1 and self.state[row][col + 1] not in ('X', 'O'):
      self.probability_grid[row][col + 1] += 10
  def is_in_bounds(self, row: int, col: int) -> bool:
    return 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE
  # NN helpers
  def get_heatmap(self, nreps, current_state):
    """
    0: unexplored
    1: hit and destroyed OR miss
    2: hit but not destroyed
    3: ship simulated
    4: ship simulated on top of undestroyed ship
    """
    # Append extra copies of a simulated board based on number of overlaps with undestroyed ships (more informative sims)
    heatmap_list = []
    for _ in range(nreps):
      test_grid = copy.deepcopy(current_state)
      num_overlaps = 0
      new_grid = False
      # Simulate ship placements on board
      for ship in self.ships_remaining:
        # Until the ship is properly placed
        attempts = 0
        while True:
          if attempts >= 500: 
            new_grid = True
            break
          attempts += 1
          # Get a coordinate value not already used
          while True:
            random_row = random.randint(0, GRID_SIZE - 1)
            random_col = random.randint(0, GRID_SIZE - 1)
            if test_grid[random_row][random_col] in (0, 2):
              anchor_row, anchor_col = random_row, random_col
              break
          # Get allowed swing points
          valid_swing_points = []
          swing_down_allowed = swing_right_allowed = swing_up_allowed = swing_left_allowed = False

          right_swing_point = anchor_col+(SHIPS_SIZES[ship]-1)
          down_swing_point = anchor_row+(SHIPS_SIZES[ship]-1)
          left_swing_point = anchor_col-(SHIPS_SIZES[ship]-1)
          up_swing_point = anchor_row-(SHIPS_SIZES[ship]-1)

          if (down_swing_point <= 9): swing_down_allowed = all(test_grid[n][anchor_col] in (0, 2) for n in range(anchor_row+1, down_swing_point+1))
          if (right_swing_point <= 9): swing_right_allowed = all(test_grid[anchor_row][n] in (0, 2) for n in range(anchor_col+1, right_swing_point+1))
          if (up_swing_point >= 0): swing_up_allowed = all(test_grid[n][anchor_col] in (0, 2) for n in range(up_swing_point, anchor_row))
          if (left_swing_point >= 0): swing_left_allowed = all(test_grid[anchor_row][n] in (0, 2) for n in range(left_swing_point, anchor_col))

          if (swing_down_allowed): valid_swing_points.append(INT_TO_STR[down_swing_point] + str(anchor_col))
          if (swing_right_allowed): valid_swing_points.append(INT_TO_STR[anchor_row] + str(right_swing_point))
          if (swing_up_allowed): valid_swing_points.append(INT_TO_STR[up_swing_point] + str(anchor_col))
          if (swing_left_allowed): valid_swing_points.append(INT_TO_STR[anchor_row] + str(left_swing_point))

          # If there are no possible swing points from the chosen anchor, then reset anchor
          if len(valid_swing_points) == 0: continue
          # Place the anchor point on the board
          if test_grid[anchor_row][anchor_col] == 0: 
            test_grid[anchor_row][anchor_col] = 3
          elif test_grid[anchor_row][anchor_col] == 2: 
            test_grid[anchor_row][anchor_col] = 4
            num_overlaps += 1
          # Set secondary point (orientations that are in bounds and do not overlap other ships)
          swing_point = valid_swing_points[random.randint(0, len(valid_swing_points) - 1)]
          swing_row, swing_col = (STR_TO_INT[swing_point[0]], int(swing_point[1]))
          # Place ship onto board
          a_x, a_y = anchor_row, anchor_col
          s_x, s_y = swing_row, swing_col
          # Horizontal orientation
          if a_y == s_y: 
            for x in range(min(a_x, s_x), max(a_x, s_x)+1): 
              if test_grid[x][a_y] == 0: 
                test_grid[x][a_y] = 3
              elif test_grid[x][a_y] == 2: 
                test_grid[x][a_y] = 4
                num_overlaps += 1
          # Vertical orientation
          if a_x == s_x:
            for y in range(min(a_y, s_y), max(a_y, s_y)+1): 
              if test_grid[a_x][y] == 0: 
                test_grid[a_x][y] = 3
              elif test_grid[a_x][y] == 0: 
                test_grid[a_x][y] = 4
                num_overlaps += 1

          break
        if new_grid: break
      
      for _ in range(num_overlaps+1):
        heatmap_list.append(test_grid)
    
    heatmap_tensor = np.array(heatmap_list)

    heatmap = np.zeros((10, 10))
    for sim in heatmap_tensor:
      for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
          if sim[row][col] == 3:
            heatmap[row][col] += 1

    return heatmap
  # Modify fog of war input
  # 0: unexplored
  # 1: hit and destroyed OR miss
  # 2: hit but not destroyed
  def transform_data(self):
    current_state = copy.deepcopy(self.fog_of_war)
    self.searching = True
    for row in range(GRID_SIZE):
      for col in range(GRID_SIZE):
        if current_state[row][col] == 'X' and any([row, col] in _ for _ in self.locations_destroyed):
          current_state[row][col] = 1
        elif current_state[row][col] == 'O':
          current_state[row][col] = 1
        elif current_state[row][col] == 'X' and not any([row, col] in _ for _ in self.locations_destroyed):
          current_state[row][col] = 2
          self.searching = False
        else:
          current_state[row][col] = 0
    return current_state
  def train_neural_network(self):
    # [(transformed state, heatmap), ...]
    with open('NeuralNetworkData', 'rb') as file:
      pairs = pickle.load(file)
  
    input_tensor_list = []
    heatmap_list = []
    for pair in pairs:
      (input_tensor, heatmap) = pair
      input_tensor_list.append(input_tensor)
      heatmap_list.append(heatmap)

    # 80:20 split
    training_data = np.array(input_tensor_list[:int(len(input_tensor_list) * 0.8)])
    training_labels = np.array(heatmap_list[:int(len(heatmap_list) * 0.8)])
    validation_data = np.array(input_tensor_list[int(len(input_tensor_list) * 0.8):])
    validation_labels = np.array(heatmap_list[int(len(heatmap_list) * 0.8):])

    # Define the model
    network = Sequential([
      Input(shape=(10, 10, 3)),
      Conv2D(25, (5, 5), activation='relu', padding="same", kernel_initializer=HeNormal(), kernel_regularizer=l2(0.01)),
      Flatten(),
      Dense(100, activation='softmax'),
      Reshape((10, 10, 1))
    ])
    
    # Compile the model
    network.compile(optimizer='adam', loss='binary_crossentropy', metrics=['mean_squared_error'])
    network.fit(training_data, training_labels, epochs=EPOCHS, verbose=0, validation_data=(validation_data, validation_labels))
    network.summary()
  
    self.network = network

  # General AI move
  #  returns a boolean, True for ship hit or False for ship not hit
  def gen_AI_move(self, style_choice: int) -> bool:
    if style_choice == 1: return self.random_move()
    if style_choice == 2: return self.human_sim_move()
    if style_choice == 3: return self.AI_mcts_move()
    if style_choice == 4: return self.neural_network_move()
    if style_choice == 5: return self.heatmap_move()

# Generate a random board for the NN to train on
#  return (transformed_board, heatmap)
def generate_random_boards_with_heatmaps():
  global probableHuman
  hold_global = probableHuman
  probableHuman = True
  num_moves_random = random.randint(0, 80)#30)
  #num_moves_probabilistic = random.randint(0, 30)

  board = BoardState()
  data = []
  for _ in range(NN_NREPS):
    for ship in SHIPS_NAMES:
      board.randomly_place_ship(ship)
    for _ in range(num_moves_random):
      board.random_move()
    # for _ in range(num_moves_probabilistic):
    #   board.human_sim_move()
    if len(board.ships_remaining) == 0: continue
    transformed_layout = board.transform_data()
    if board.searching: data.append((transformed_layout, board.get_probability_grid()))
    else: data.append((transformed_layout, board.get_heatmap(nreps=H_NREPS, current_state=transformed_layout)))
    board.reset()
  
  probableHuman = hold_global

  return data

# Player chooses if they want to play a game or test the AI
def choose_play_or_test() -> int:
  while True:
    clear_console()
    print("Would you like to play a game against AI or test AI move efficiencies?")
    choice = input("Play against AI: 1\nTest efficiencies: 2\n")
    if choice == '1': return 1
    if choice == '2': return 2
# Player chooses which AI they want to play against / test
def choose_AI_type(choice: int) -> int:
    # Player choose form of AI move style
    if choice == 1:
        input_string = "play against"
    else:
        input_string = "test"
    while True:
        clear_console()
        print(f"Select the type of AI you want to {input_string}.")
        print("Random moves: 1")
        print("Simulated player (even strategy): 2")
        print("Simulated player (probabilistic strategy): 3")
        print("Monte Carlo Simulation: 4")
        print("Neural Network: 5")
        print("Heatmap: 6")
        choice = input()
        if choice == '1': return 1
        if choice == '2': return 2
        if choice == '3':
            global probableHuman
            probableHuman = True
            return 2
        if choice == '4': return 3
        if choice == '5': return 4
        if choice == '6': return 5
    
# Print the user interface for each turn
def print_UI(player_grid, AI_grid, player_move_result: str, AI_move_result: str) -> None:
  # Show results of previous turn (or help messages if on first turn)
  #clear_console()
  print(player_move_result)
  print(AI_move_result)
  # Show both grids to player with proper fog of war
  print("Your grid")
  player_grid.print_grid(fog_of_war=False)
  print("Enemy grid")
  AI_grid.print_grid(fog_of_war=True)
# Print end of game message
def print_end_message(player_grid, AI_grid, player_win: bool, move_count: int) -> None:
  clear_console()
  if player_win:
    print("YOU WON")
    print("It took you " + str(move_count) + " moves to win.")
  else:
    print("YOU LOST")
    print("It took the AI " + str(move_count) + " moves to win.")
  print("Your grid")
  player_grid.print_grid(fog_of_war=False)
  print("Enemy grid")
  AI_grid.print_grid(fog_of_war=True)

# Generate NN data
def generate_data():
  # [(input_tensor, heatmap), (input_tensor, heatmap), ...]  
  new_pairs = generate_random_boards_with_heatmaps()
  random_board_list = []
  heatmap_list = []

  for pair in new_pairs:
    random_board, heatmap = pair
    random_board_list.append(random_board)
    heatmap_list.append(heatmap)

  # Transform random boards to a list of one-hot 3D representations
  # layer 0: unexplored
  # layer 1: hit and destroyed OR miss
  # layer 2: hit but not destroyed
  input_tensor_list = []
  for random_board in random_board_list:
    input_tensor = np.zeros((GRID_SIZE, GRID_SIZE, 3))
    for row in range(GRID_SIZE):
      for col in range(GRID_SIZE):
        if random_board[row][col] == 0:
          input_tensor[row][col][0] = 1
        if random_board[row][col] == 1:
          input_tensor[row][col][1] = 1
        if random_board[row][col] == 2:
          input_tensor[row][col][2] = 1
        input_tensor_list.append(input_tensor)

  # Create a new list for the new pairs
  new_pairs_transformed = [(input_tensor_list[i], heatmap_list[i]) for i in range(len(new_pairs))]

  # Append to current list and write to file
  with open('NeuralNetworkData', 'rb') as file:
    pairs = pickle.load(file)
  for i in range(len(new_pairs_transformed)):
    pairs.append(new_pairs_transformed[i])
  with open('NeuralNetworkData', 'wb') as file:
    pickle.dump(pairs, file)

  print(f"{len(pairs)} pairings (tensor input, heatmap) in data.")

def main():
  if GENERATE_DATA: 
    generate_data()
    return 0
  
  # with open('NeuralNetworkMoves', 'rb') as file:
  #   previous_rep_history = pickle.load(file)  
  # print(previous_rep_history)
  # print(len(previous_rep_history))
  # return 0

  global humanSimSunkResult
  # Check whether the user wants to play a game or test the AI
  play_or_test = choose_play_or_test()
  
  # If the user wants to play against the AI
  if play_or_test == 1:
    # Initialize the player grid
    player_grid = BoardState()
    while True:
      place_own_ships = input("Would you like to place your own ships (y/n): ")
      # If the player wants to place their own ships
      if place_own_ships in ("y", "Y", "Yes", "yes"): 
        for ship_name in SHIPS_NAMES: player_grid.place_ship(ship_name)
        break
      # If the player wants to a randomly generated layout
      if place_own_ships in ("n", "N", "No", "no"):
        for ship_name in SHIPS_NAMES: player_grid.randomly_place_ship(ship_name)
        break
    # Initialize the adversary grid
    AI_grid = BoardState()
    for ship_name in SHIPS_NAMES: AI_grid.randomly_place_ship(ship_name)

    # Player choose form of AI move style
    style_choice = choose_AI_type(play_or_test)

    # These messages will appear at the top of the screen during each turn,
    #  so before the first turn there will be some help messages
    player_move_result = "Your board is on top and will be updated as your opponent makes moves."
    AI_move_result = "Your moves will appear on the bottom board."

    # Track number of moves for each player
    count_player = 0
    count_AI = 0

    # Run turns of the game until someone wins
    while True:
      print_UI(player_grid, AI_grid, player_move_result, AI_move_result)

      # Player move executed on opponent's board
      AI_check_ship_hit = AI_grid.player_move()
      player_move_result = "You hit an enemy ship!" if AI_check_ship_hit else "You missed."
      # Check if an enemy ship has been sunk from the player's previous move
      AI_ship_sunk = AI_grid.check_ship_sunk()
      player_move_result = "You sunk the enemy " + AI_ship_sunk + "!" if AI_ship_sunk != "" else player_move_result
      count_player += 1
      # Check if the player has won
      if len(AI_grid.ships_remaining) == 0: 
        print_end_message(player_grid, AI_grid, False, count_player)
        break

      # Make AI move according to player choice
      player_check_ship_hit = player_grid.gen_AI_move(style_choice)
      AI_move_result = "The enemy has hit one of your ships!" if player_check_ship_hit else "The enemy missed."
      # Check if a friendly ship has been sunk from the opponent's previous move
      result = player_grid.check_ship_sunk()
      humanSimSunkResult = result
      player_ship_sunk = result
      AI_move_result = "The enemy has sunk your " + player_ship_sunk + "!" if player_ship_sunk != "" else AI_move_result
      count_AI += 1
      # Check if the opponent has won
      if len(player_grid.ships_remaining) == 0: 
        print_end_message(player_grid, AI_grid, False, count_AI)
        break

  # If the user wants to test the AI
  if play_or_test == 2:
    # Player choose form of AI move style
    style_choice = choose_AI_type(play_or_test)

    nreps = NREPS
    test_grid = BoardState()
    # Will hold number of moves for each rep
    rep_history = []
    # Get all simulation data
    for i in range(nreps):
      # Reset the board with new ship placements
      test_grid.reset()
      for ship_name in SHIPS_NAMES: test_grid.randomly_place_ship(ship_name)
      # Reset the number of moves
      count_AI = 0
      # Simulate a game
      while True:
        # Make AI move according to player choice
        try: 
          _ = test_grid.gen_AI_move(style_choice)
        except:
          continue
        count_AI += 1
        # Needed to update ships_remaining 
        result = test_grid.check_ship_sunk()
        humanSimSunkResult = result
        _ = result
        # Check if the AI has won
        if len(test_grid.ships_remaining) == 0: 
          rep_history.append(count_AI)
          break
    # NN is compute-heavy so its reps are stored
    if style_choice == 4:
      with open('NeuralNetworkMoves', 'rb') as file:
        previous_rep_history = pickle.load(file)  
      for i in range(len(rep_history)):
        previous_rep_history.append(rep_history[i])
      with open('NeuralNetworkMoves', 'wb') as file:
        pickle.dump(previous_rep_history, file)
      rep_history = previous_rep_history
      nreps = len(rep_history) # because nreps is used in the avg calculation
    # Heatmap is compute-heavy so its reps are stored
    if style_choice == 5:
      with open('HeatmapMoves', 'rb') as file:
        previous_rep_history = pickle.load(file)  
      for i in range(len(rep_history)):
        previous_rep_history.append(rep_history[i])
      with open('HeatmapMoves', 'wb') as file:
        pickle.dump(rep_history, file)
      rep_history = previous_rep_history
      nreps = len(rep_history) # because nreps is used in the avg calculation
    # After all testing, show average moves for the AI to win
    clear_console()
    print(f"It took the AI {sum(rep_history)/nreps} moves on average to win!")

if __name__ == "__main__":
  main()
