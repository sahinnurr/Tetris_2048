################################################################################
#                                                                              #
# The main program of Tetris 2048 Base Code                                    #
#                                                                              #
################################################################################


import lib.stddraw as stddraw  # for creating an animation with user interactions
import tile
from lib.picture import Picture  # used for displaying an image on the game menu
from lib.color import Color  # used for coloring the game menu
import os  # the os module is used for file and directory operations
from game_grid import GameGrid  # the class for modeling the game grid
from tetromino import Tetromino  # the class for modeling the tetrominoes
import random  # used for creating tetrominoes with random types (shapes)
import numpy as np
from point import Point # used for tile positions
from tile import Tile  # used for modeling each tile on the tetrominoes
import pygame as pg # ONLY FOR MUSICS AND SOUND EFFECTS

# The main function where this program starts execution
def start():
   # set the dimensions of the game grid
   grid_h, grid_w = 20, 12
   # set the extra part's width right next to the grid
   extra_w = 6
   # set the size of the drawing canvas (the displayed window)
   canvas_h, canvas_w = 40 * grid_h, 40 * (grid_w + extra_w)
   stddraw.setCanvasSize(canvas_w, canvas_h)
   # set the scale of the coordinate system for the drawing canvas
   stddraw.setXscale(-0.5, (grid_w + extra_w) - 0.5)
   stddraw.setYscale(-0.5, grid_h - 0.5)

   # set the game grid dimension values stored and used in the Tetromino class
   Tetromino.grid_height = grid_h
   Tetromino.grid_width = grid_w
   # create the game grid
   grid = GameGrid(grid_h, grid_w)
   # display a simple menu before opening the game
   # by using the display_game_menu function defined below
   display_game_menu(grid)

def update(grid):
   # Resetting grid
   grid = GameGrid(grid.grid_height, grid.grid_width)
   # Creating the first and next tetromino and assigning them to appropriate variables
   current_tetromino = create_tetromino()
   next_tetromino = create_tetromino()
   grid.current_tetromino = current_tetromino
   grid.next_tetromino = next_tetromino
   # Initializing Game Music
   current_dir = os.path.dirname(os.path.realpath(__file__))
   game_music_file = current_dir + "/sounds/tetris-theme.wav"
   pg.mixer.init()
   pg.mixer.music.load(game_music_file)
   pg.mixer.music.set_volume(grid.player.getVolume() / 100)
   if (grid.player.getMusicCondition()):
      # Playing Menu Music Forever
      pg.mixer.music.play(-1)
   # the main game loop
   music_paused = False
   while True:
      if stddraw.mousePressed():
         mouse_x, mouse_y = stddraw.mouseX(), stddraw.mouseY() #get the coordinates of mouse that has been clicked
         # check if these coordinates are inside the pause button
         if mouse_x >= 13.5 and mouse_x <= 15.5:
            if mouse_y >= 10.5 and mouse_y <= 11.5:
               playClickSound(grid.player)
               pg.mixer.music.set_volume(0)
               display_pause_menu(grid)
               pg.mixer.music.set_volume(grid.player.getVolume() / 100)
      # check for any user interaction via the keyboard
      if stddraw.hasNextKeyTyped():  # check if the user has pressed a key
         key_typed = stddraw.nextKeyTyped()  # the most recently pressed key
         # if the left arrow key has been pressed
         if key_typed == "left":
            # move the active tetromino left by one
            current_tetromino.move(key_typed, grid)
         # if the right arrow key has been pressed
         elif key_typed == "right":
            # move the active tetromino right by one
            current_tetromino.move(key_typed, grid)
         # if the down arrow key has been pressed
         elif key_typed == "down":
            # move the active tetromino down by one
            # (soft drop: causes the tetromino to fall down faster)
            current_tetromino.move(key_typed, grid)
         elif key_typed == "r" or key_typed == "up":
            # Rotates the tetromino when R key or up key pressed
            current_tetromino.rotate(grid)
         elif key_typed == "space":
            # hard drop: causes the tetromino to fall down to the bottom
            while current_tetromino.can_be_moved("down", grid):
               current_tetromino.move("down", grid)

         # clear the queue of the pressed keys for a smoother interaction
         stddraw.clearKeysTyped()

      # move the active tetromino down by one at each iteration (auto fall)
      success = current_tetromino.move("down", grid)
      game_over = grid.game_over

      if game_over:
         break

      # lock the active tetromino onto the grid when it cannot go down anymore
      if not success:
         # get the tile matrix of the tetromino without empty rows and columns
         # and the position of the bottom left cell in this matrix
         tiles, pos = current_tetromino.get_min_bounded_tile_matrix(True)
         # update the game grid by locking the tiles of the landed tetromino
         game_over = grid.update_grid(tiles, pos)
         # end the main game loop if the game is over
         if game_over:
            break
         # check for merges when tetromino stopped
         apply_merge(grid)
         grid.clear_tiles()
         # Assigning the next tetromino to current tetromino to be able to draw it on the game grid
         current_tetromino = grid.next_tetromino
         grid.current_tetromino = current_tetromino
         # Modifying next_tetromino with a new random tetromino
         grid.next_tetromino = create_tetromino()

         # Keep row information if they are completely filled or not
         row_count = is_full(grid.grid_height, grid.grid_width, grid)
         index = 0
         # Shift down the rows
         while index < grid.grid_height:
            while row_count[index]:
               shift_down(row_count, grid)
               row_count = is_full(grid.grid_height, grid.grid_width, grid)
            index += 1

         # Assign labels to each tile using 4-component labeling
         labels, num_labels = connected_component_labeling(grid.tile_matrix, grid.grid_width, grid.grid_height)
         # Find free tiles and drop down the ones not connected to others
         free_tiles = [[False for v in range(grid.grid_width)] for b in range(grid.grid_height)]
         free_tiles, num_free = search_free_tiles(grid.grid_height, grid.grid_width, labels, free_tiles)
         grid.move_free_tiles(free_tiles)

         # Drops down tiles that don't connect any other tiles until there is no tile to drop down
         while num_free != 0:
            labels, num_labels = connected_component_labeling(grid.tile_matrix, grid.grid_width, grid.grid_height)
            free_tiles = [[False for v in range(grid.grid_width)] for b in range(grid.grid_height)]
            free_tiles, num_free = search_free_tiles(grid.grid_height, grid.grid_width, labels, free_tiles)
            grid.move_free_tiles(free_tiles)

         labels, num_labels = connected_component_labeling(grid.tile_matrix, grid.grid_width, grid.grid_height)
         grid.clear_tiles()

      # display the game grid with the current tetromino
      grid.display()

   # Updating high score after game is over
   if (grid.score > grid.player.getHighScore()):
      grid.player.setHighScore(grid.score)
   # Updating save file
   grid.player.updateOnClose()
   # print a message on the console when the game is over
   display_game_over_menu(grid)


# A function for creating random shaped tetrominoes to enter the game grid
def create_tetromino():
   # the type (shape) of the tetromino is determined randomly
   tetromino_types = ['I', 'O', 'Z', 'L', 'J', 'S', 'T']
   random_index = random.randint(0, len(tetromino_types) - 1)
   random_type = tetromino_types[random_index]
   # create and return the tetromino
   tetromino = Tetromino(random_type)
   return tetromino

# A function for displaying a simple menu before starting the game
def display_game_menu(grid):
   # Initializing height, weight and player variables
   grid_height = grid.grid_height
   grid_width = grid.grid_width
   player = grid.player
   # the colors used for the menu
   background_color = Color(42, 69, 99)
   button_color = Color(25, 255, 228)
   text_color = Color(31, 160, 239)
   # clear the background drawing canvas to background_color
   stddraw.clear(background_color)
   # get the directory in which this python code file is placed
   current_dir = os.path.dirname(os.path.realpath(__file__))
   # compute the path of the image file
   img_file = current_dir + "/images/menu_image.png"
   # the coordinates to display the image centered horizontally
   img_center_x, img_center_y = (grid_width + 6 - 1) / 2, grid_height - 7 # +6 is extra part's width
   # the image is modeled by using the Picture class
   image_to_display = Picture(img_file)
   # add the image to the drawing canvas
   stddraw.picture(image_to_display, img_center_x, img_center_y)
   # Initializing Menu Music
   menu_music_file = current_dir + "/sounds/menu-music.wav"
   pg.mixer.init()
   pg.mixer.music.load(menu_music_file)
   pg.mixer.music.set_volume(grid.player.getVolume() / 100)
   # Playing Menu Music Forever
   if (grid.player.getMusicCondition()):
      pg.mixer.music.play(-1)
   # the dimensions for the start game button
   button_w, button_h = grid_width - 1.5, 2
   # the coordinates of the bottom left corner for the start game button
   button_blc_x, button_blc_y = img_center_x - button_w / 2, 4
   # add the start game button as a filled rectangle
   stddraw.setPenColor(button_color)
   stddraw.filledRectangle(button_blc_x, button_blc_y, button_w, button_h)
   # add the text on the start game button
   stddraw.setFontFamily("Arial")
   stddraw.setFontSize(25)
   stddraw.setPenColor(text_color)
   text_to_display = "Click Here to Start the Game"
   stddraw.text(img_center_x, 5, text_to_display)
   # Settings Button
   s_button_w, s_button_h = 2, 2
   s_button_blc_x, s_button_blc_y = img_center_x - s_button_w / 2, 1
   stddraw.setPenColor(button_color)
   stddraw.filledRectangle(s_button_blc_x, s_button_blc_y, s_button_w, s_button_h)
   stddraw.setPenColor(text_color)
   stddraw.text(img_center_x, 2, "Settings")
   # the user interaction loop for the simple menu
   while True:
      # display the menu and wait for a short time (50 ms)
      stddraw.show(50)
      # check if the mouse has been left-clicked on the start game button
      if stddraw.mousePressed():
         # get the coordinates of the most recent location at which the mouse
         # has been left-clicked
         mouse_x, mouse_y = stddraw.mouseX(), stddraw.mouseY()
         # check if these coordinates are inside the settings button
         if mouse_x >= s_button_blc_x and mouse_x <= s_button_blc_x + s_button_w:
            if mouse_y >= s_button_blc_y and mouse_y <= s_button_blc_y + s_button_h:
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               display_settings_menu(grid) # Opens the settings page
         # check if these coordinates are inside the start button
         if mouse_x >= button_blc_x and mouse_x <= button_blc_x + button_w:
            if mouse_y >= button_blc_y and mouse_y <= button_blc_y + button_h:
               pg.mixer.music.stop()
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               update(grid)  # break the loop to end the method and start the game

# A function for displaying a settings menu before starting the game
def display_settings_menu(grid):
   # Initializing height, weight and player variables
   grid_height = grid.grid_height
   grid_width = grid.grid_width
   player = grid.player
   # the colors used for the menu
   background_color = Color(42, 69, 99)
   button_color = Color(25, 255, 228)
   text_color = Color(31, 160, 239)
   # get the directory in which this python code file is placed
   current_dir = os.path.dirname(os.path.realpath(__file__))
   while True:
      # clear the background drawing canvas to background_color
      stddraw.clear(background_color)
      img_center_x, img_center_y = (grid_width + 6 - 1) / 2, grid_height - 7 # +6 is extra part's width
      # Volume Text
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x - 6, 15, "Music Volume")
      # Increase Button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(img_center_x + 7, 14.7, 0.5, 0.5)
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x + 7.25, 15, "+")
      # Decrease Button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(img_center_x + 5, 14.7, 0.5, 0.5)
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x + 5.25, 15, "-")
      # Music Text
      stddraw.text(img_center_x - 6, 13, "Music")
      # Difficulty Text
      stddraw.text(img_center_x - 6, 11, "Difficulty")
      # Difficulty Level Text
      difficulty_level_text = ""
      if player.getDiff() == 0:
         difficulty_level_text = "Easy"
      elif player.getDiff() == 1:
         difficulty_level_text = "Normal"
      elif player.getDiff() == 2:
         difficulty_level_text = "Hard"
      stddraw.setPenColor(button_color)
      stddraw.text(img_center_x + 6.2, 11, difficulty_level_text)
      # Difficulty Right
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(img_center_x + 7.5, 10.7, 0.5, 0.5)
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x + 7.75, 11, "->")
      # Difficulty Left
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(img_center_x + 4.5, 10.7, 0.5, 0.5)
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x + 4.75, 11, "<-")
      # Back Button
      b_button_w, b_button_h = 2, 2
      b_button_blc_x, b_button_blc_y = img_center_x - b_button_w / 2, 1
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(b_button_blc_x, b_button_blc_y, b_button_w, b_button_h)
      stddraw.setPenColor(text_color)
      stddraw.text(img_center_x, 2, "Start")
      # Music On-Off Button
      if (player.getMusicCondition()):
         stddraw.setPenColor(Color(9, 255, 0))
      else:
         stddraw.setPenColor(Color(255, 0, 42))
      stddraw.filledRectangle(img_center_x + 6, 12.7, 0.5, 0.5)
      # Music Volume
      stddraw.setPenColor(button_color)
      stddraw.text(img_center_x + 6.2, 15, str(player.getVolume()))
      # check if the mouse has been left-clicked on the any button
      if stddraw.mousePressed():
         # get the coordinates of the most recent location at which the mouse
         # has been left-clicked
         mouse_x, mouse_y = stddraw.mouseX(), stddraw.mouseY()
         # check if these coordinates are inside the music volume increase button
         if mouse_x >= img_center_x + 7 and mouse_x <= img_center_x + 7 + 2:
            if mouse_y >= 14 and mouse_y <= 15.3:
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               player.increaseVolume(5)
               pg.mixer.music.set_volume(grid.player.getVolume() / 100)
         # check if these coordinates are inside the music volume decrease button
         if mouse_x >= img_center_x + 5 and mouse_x <= img_center_x + 6:
            if mouse_y >= 14 and mouse_y <= 15.3:
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               player.decreaseVolume(5)
               pg.mixer.music.set_volume(grid.player.getVolume() / 100)
         # check if these coordinates are inside the difficulty right button
         if mouse_x >= img_center_x + 7.5 and mouse_x <= img_center_x + 8:
            if mouse_y >= 10 and mouse_y <= 11:
               if (player.getDiff() <= 1):
                  # Initializing and Playing Click Sound
                  playClickSound(grid.player)
                  player.setDiff(player.getDiff() + 1)
         # check if these coordinates are inside the difficulty left button
         if mouse_x >= img_center_x + 4.5 and mouse_x <= img_center_x + 5:
            if mouse_y >= 10 and mouse_y <= 11:
               if (player.getDiff() >= 1):
                  # Initializing and Playing Click Sound
                  playClickSound(grid.player)
                  player.setDiff(player.getDiff() - 1)
         # check if these coordinates are inside the music on-off button
         if mouse_x >= img_center_x + 6 and mouse_x <= img_center_x + 6 + 2:
            if mouse_y >= 12 and mouse_y <= 14:
               if (player.getMusicCondition()):
                  player.turnMusicOff()
                  pg.mixer.music.set_volume(0)
               else:
                  # Initializing and Playing Click Sound
                  playClickSound(grid.player)
                  player.turnMusicOn()
                  pg.mixer.music.set_volume(grid.player.getVolume() / 100)
         # check if these coordinates are inside the start button
         if mouse_x >= b_button_blc_x and mouse_x <= b_button_blc_x + b_button_w:
            if mouse_y >= b_button_blc_y and mouse_y <= b_button_blc_y + b_button_h:
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               player.updateOnClose()
               update(grid)
      # display the menu and wait for a short time (50 ms)
      stddraw.show(50)

def display_game_over_menu(grid):
   # Initializing height, weight and player variables
   grid_height = grid.grid_height
   grid_width = grid.grid_width
   # the colors used for the menu
   background_color = Color(42, 69, 99)
   button_color = Color(25, 255, 228)
   text_color = Color(31, 160, 239)
   # Initializing and Playing Game Over Sound
   playGameOverSound(grid.player)
   while True:
      # clear the background drawing canvas to background_color
      stddraw.clear(background_color)
      img_center_x, img_center_y = (grid_width + 6 - 1) / 2, grid_height - 7 # +6 is extra part's width
      # Changing Font Size for Game Over and Score Texts
      stddraw.setFontSize(70)
      # Game Over Text
      stddraw.setPenColor(Color(255, 255, 255))
      stddraw.text(img_center_x, 15, "GAME OVER")
      # Score Text
      stddraw.setPenColor(Color(255, 255, 255))
      stddraw.text(img_center_x, 12, "SCORE: " + str(grid.score))
      if grid.score < 2048:
         stddraw.setPenColor(Color(255, 255, 255))
         stddraw.setFontSize(40)
         stddraw.text(img_center_x, 10, "YOU LOSE!")
      elif grid.score >= 2048 or grid.win_condition_met:
         stddraw.setPenColor(Color(255, 255, 255))
         stddraw.setFontSize(40)
         stddraw.text(img_center_x, 10, "YOU WIN!")
      # Changing Font Size for Button Texts
      stddraw.setFontSize(35)
      # Restart Button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(img_center_x - 7, 3, 4, 2)
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x - 5, 4, "Restart")
      # Main Menu Button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(img_center_x - 2, 3, 4, 2)
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x, 4, "Main Menu")
      # Settings Button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(img_center_x + 3, 3, 4, 2)
      stddraw.setPenColor(Color(0, 0, 0))
      stddraw.text(img_center_x + 5, 4, "Settings")
      # check if the mouse has been left-clicked on the any button
      if stddraw.mousePressed():
         # get the coordinates of the most recent location at which the mouse
         # has been left-clicked
         mouse_x, mouse_y = stddraw.mouseX(), stddraw.mouseY()
         # check if these coordinates are inside the restart button
         if mouse_x >= img_center_x - 7 and mouse_x <= img_center_x -3:
            if mouse_y >= 3 and mouse_y <= 5:
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               update(grid)
         # check if these coordinates are inside the main menu button
         if mouse_x >= img_center_x -2 and mouse_x <= img_center_x + 2:
            if mouse_y >= 3 and mouse_y <= 5:
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               display_game_menu(grid)
         # check if these coordinates are inside the settings button
         if mouse_x >= img_center_x + 3 and mouse_x <= img_center_x + 7:
            if mouse_y >= 3 and mouse_y <= 5:
               # Initializing and Playing Click Sound
               playClickSound(grid.player)
               display_settings_menu(grid)
      # display the menu and wait for a short time (50 ms)
      stddraw.show(50)

# Checks each row if they are completely filled with tiles and returns each row in an array
# If a row is completely filled, it takes True value; otherwise, False
def is_full(grid_h, grid_w, grid):
   # Creates an array with all False values, with size equal to the number of rows in the game grid
   row_count = [False for _ in range(grid_h)]
   # If a row is full, this score variable keeps the total score which will come from this full row
   score = 0
   for h in range(grid_h):
      # Keeps track of the total number of tiles inside the same row; if counter == grid_w, the row is full
      counter = 0
      for w in range(grid_w):
         if grid.is_occupied(h, w):
            counter += 1
         # If the row is full, calculates the total score in this row
         if counter == grid_w:
            score = sum(grid.tile_matrix[h][a].number for a in range(grid_w))
            row_count[h] = True
   # Updates the total score
   grid.score += score
   return row_count

# Moves each tile by one unit down if it is available
def shift_down(row_count, grid):
   for index, i in enumerate(row_count):
      if i:
         for a in range(index, 19):
            row = np.copy(grid.tile_matrix[a + 1])
            grid.tile_matrix[a] = row
            for b in range(12):
               if grid.tile_matrix[a][b] is not None:
                  grid.tile_matrix[a][b].move(0, -1)
         break

# Searches and finds tiles which do not connect to others
def search_free_tiles(grid_h, grid_w, labels, free_tiles):
   counter = 0
   ready_labels = []
   for x in range(grid_h):
      for y in range(grid_w):
         if labels[x, y] != 1 and labels[x, y] != 0:
            if x == 0:
               ready_labels.append(labels[x, y])
               if not ready_labels.count(labels[x, y]):
                  free_tiles[x][y] = True
                  counter += 1
   return free_tiles, counter

def shift_down_free_tiles(grid):
   for r in range(grid.grid_height):
      for c in range(grid.grid_width):
         if c == 0 and r - 1 >= 0:
            if grid.tile_matrix[r - 1][c] is None and grid.tile_matrix[r][c + 1] is None and grid.tile_matrix[r][c] is not None:
               grid.tile_matrix[r][c].position = (r, c-1)
         elif c == grid.grid_width - 1:
            if grid.tile_matrix[r - 1][c] is None and grid.tile_matrix[r][c - 1] is None and grid.tile_matrix[r][c] is not None:
               grid.tile_matrix[r][c].position = (r, c-1)
         else:
            if grid.tile_matrix[r - 1][c] is None and grid.tile_matrix[r][c - 1] is None and grid.tile_matrix[r][c + 1] is None and grid.tile_matrix[r][c] is not None:
               grid.tile_matrix[r][c].position = (r, c-1)


def apply_merge(grid):
    height = grid.grid_height
    width = grid.grid_width
    merged = False
    while True:
        # Flag to track if any merging occurred in this iteration
        merged_this_iteration = False
        # Iterate over each column
        for column in range(width):
            # Flag to track if any tile was moved down in this column
            moved_down = False
            # Iterate over each row from top to bottom
            for row in range(1, height):
                # Skip if the current tile is empty
                if grid.tile_matrix[row][column] is None:
                    continue
                # If the tile below is empty, move the current tile down
                if grid.tile_matrix[row - 1][column] is None:
                    grid.tile_matrix[row - 1][column] = grid.tile_matrix[row][column]
                    grid.tile_matrix[row][column] = None
                    moved_down = True
            # Merge tiles in this column
            row = 0
            while row < height - 1:
                # Skip if the current tile or the tile below is empty
                if grid.tile_matrix[row][column] is None or grid.tile_matrix[row + 1][column] is None:
                    row += 1
                    continue
                # Merge vertically if the tile below has the same number
                if grid.tile_matrix[row][column].number == grid.tile_matrix[row + 1][column].number:
                    # Double the number of the current tile
                    grid.tile_matrix[row][column].number *= 2
                    # Increase score
                    grid.score += grid.tile_matrix[row][column].number
                    # Remove the tile below
                    grid.tile_matrix[row + 1][column] = None
                    # Update color if necessary
                    updateColor(grid.tile_matrix[row][column], grid.tile_matrix[row][column].number)
                    merged_this_iteration = True  # Set the flag to True
                    row += 1
                else:
                    row += 1
        # If no merging or movement occurred in this iteration, break the loop
        if not moved_down and not merged_this_iteration:
            break
        merged = True

def updateColor(tile, num):
   colors = {
         2: (238, 228, 218),  # lightgray
         4: (236, 224, 200),  # lightblue
         8: (243, 177, 121),  # orange
         16: (245, 149, 99),  # coral
         32: (246, 124, 95),  # red
         64: (246, 94, 59),  # purple
         128: (237, 207, 114),  # green
         256: (237, 204, 97),  # blue
         512: (237, 200, 80),  # etc.
         1024: (237, 197, 63),
         2048: (237, 194, 46),
      }
   if num in colors:
      # Update the colors by num value
      color = colors[num]
      tile.background_color = Color(color[0], color[1], color[2])
      tile.foreground_color = Color(138, 129, 120)

def connected_component_labeling(grid, grid_width, grid_height):
   # First, all pixels in the image are initialized as 0
   labels = np.zeros([grid_height, grid_width], dtype=int)
   # A list to store the minimum equivalent label for each label.
   min_equivalent_labels = []
   # Labeling starts from 1 (0 represents the background of the image).
   current_label = 1

   # Assign initial labels and determine minimum equivalent labels for each pixel in the given binary image.
   for y in range(grid_height):
      for x in range(grid_width):
         if grid[y, x] is None:
            continue
         neighbor_labels = get_neighbor_labels(labels, (x, y))
         if len(neighbor_labels) == 0:
            labels[y, x] = current_label
            current_label += 1
            min_equivalent_labels.append(labels[y, x])
         else:
            labels[y, x] = min(neighbor_labels)
            if len(neighbor_labels) > 1:
               labels_to_merge = set()
               for l in neighbor_labels:
                  labels_to_merge.add(min_equivalent_labels[l - 1])
               update_min_equivalent_labels(min_equivalent_labels, labels_to_merge)

   # Rearrange equivalent labels so they all have consecutive values.
   rearrange_min_equivalent_labels(min_equivalent_labels)

   # Assign the minimum equivalent label of each pixel as its own label.
   for y in range(grid_height):
      for x in range(grid_width):
         if grid[y, x] is None:
            continue
         labels[y, x] = min_equivalent_labels[labels[y, x] - 1]

   # Return the labels matrix and the number of different labels.
   return labels, len(set(min_equivalent_labels))


# Function to get labels of the neighbors of a given pixel.
def get_neighbor_labels(label_values, pixel_indices):
   x, y = pixel_indices
   neighbor_labels = set()
   if y != 0 and label_values[y - 1, x] != 0:
      neighbor_labels.add(label_values[y - 1, x])
   if x != 0 and label_values[y, x - 1] != 0:
      neighbor_labels.add(label_values[y, x - 1])
   return neighbor_labels


# Function to update minimum equivalent labels by merging conflicting neighbor labels as the smallest value among their min equivalent labels.
def update_min_equivalent_labels(all_min_eq_labels, min_eq_labels_to_merge):
   min_value = min(min_eq_labels_to_merge)
   for index in range(len(all_min_eq_labels)):
      if all_min_eq_labels[index] in min_eq_labels_to_merge:
         all_min_eq_labels[index] = min_value


# Function to rearrange minimum equivalent labels so they all have consecutive values starting from 1.
def rearrange_min_equivalent_labels(min_equivalent_labels):
   # find different values of min equivalent labels and sort them in increasing order
   different_labels = set(min_equivalent_labels)
   different_labels_sorted = sorted(different_labels)
   # create an array for storing new (consecutive) values for min equivalent labels
   new_labels = np.zeros(max(min_equivalent_labels) + 1, dtype=int)
   count = 1  # first label value to assign
   # for each different label value (sorted in increasing order)
   for l in different_labels_sorted:
      # determine the new label
      new_labels[l] = count
      count += 1  # increase count by 1 so that new label values are consecutive
   # assign new values of each minimum equivalent label
   for ind in range(len(min_equivalent_labels)):
      old_label = min_equivalent_labels[ind]
      new_label = new_labels[old_label]
      min_equivalent_labels[ind] = new_label

def playClickSound(player):
   current_dir = os.path.dirname(os.path.realpath(__file__))
   # Initializing Click Sound
   click_sound_file = current_dir + "/sounds/tetris-click-sound.wav"
   pg.mixer.init()
   click = pg.mixer.Sound(click_sound_file)
   click.set_volume(player.getVolume() / 100)
   # Playing Sound Once
   if (player.getMusicCondition()):
      click.play()

def playGameOverSound(player):
   current_dir = os.path.dirname(os.path.realpath(__file__))
   # Initializing Click Sound
   game_over_sound_file = current_dir + "/sounds/tetris-game-over.wav"
   pg.mixer.init()
   pg.mixer.music.load(game_over_sound_file)
   pg.mixer.music.set_volume(player.getVolume() / 100)
   # Playing Sound Once
   if (player.getMusicCondition()):
      pg.mixer.music.play()

def display_pause_menu(grid):
      grid_width = grid.grid_width
      grid_height = grid.grid_height
      background_color = Color(42, 69, 99)
      button_color = Color(25, 255, 228)
      text_color = Color(31, 160, 239)
      button_width = 5
      button_height = 2
      continue_button_center_x = grid_width / 2 + 3
      continue_button_center_y = grid_height / 2 + 5
      restart_button_center_x = grid_width / 2 + 3
      restart_button_center_y = grid_height / 2
      exit_button_center_x = grid_width / 2 + 3
      exit_button_center_y = grid_height / 2 -5

      # Draw the pause menu background
      stddraw.clear(background_color)

      # Draw the "Continue" button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(continue_button_center_x - button_width / 2, continue_button_center_y - button_height / 2,
                           button_width, button_height)
      stddraw.setPenColor(text_color)
      stddraw.text(continue_button_center_x, continue_button_center_y, "Continue")

      # Draw the "Restart" button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(restart_button_center_x - button_width / 2, restart_button_center_y - button_height / 2,
                              button_width, button_height)
      stddraw.setPenColor(text_color)
      stddraw.text(restart_button_center_x, restart_button_center_y, "Restart")

      # Draw the "Exit" button
      stddraw.setPenColor(button_color)
      stddraw.filledRectangle(exit_button_center_x - button_width / 2, exit_button_center_y - button_height / 2,
                           button_width, button_height)
      stddraw.setPenColor(text_color)
      stddraw.text(exit_button_center_x, exit_button_center_y, "Exit")

      while True:
         stddraw.show(50)
         if stddraw.mousePressed():
            mouse_x, mouse_y = stddraw.mouseX(), stddraw.mouseY()
            # Check if "Continue" button is clicked
            if (continue_button_center_x - button_width / 2 <= mouse_x <= continue_button_center_x + button_width / 2) and \
                  (
                         continue_button_center_y - button_height / 2 <= mouse_y <= continue_button_center_y + button_height / 2):
               playClickSound(grid.player)
               break  # Exit the pause screen and resume the game
            # Check if "Restart" button is clicked
            if (restart_button_center_x - button_width / 2 <= mouse_x <= restart_button_center_x + button_width / 2) and \
                    (restart_button_center_y - button_height / 2 <= mouse_y <= restart_button_center_y + button_height / 2):
               playClickSound(grid.player)
               update(grid)
            # Check if "Exit" button is clicked
            if (exit_button_center_x - button_width / 2 <= mouse_x <= exit_button_center_x + button_width / 2) and \
                 (exit_button_center_y - button_height / 2 <= mouse_y <= exit_button_center_y + button_height / 2):
               playClickSound(grid.player)
               grid.game_over = True  # Set the game to end
               display_game_menu(grid) # Exit the pause screen


# start() function is specified as the entry point (main function) from which
# the program starts execution

if __name__ == '__main__':
   start()
