# Tic-Tac-Toe-Robot

## How it plays

This robot can play the game tic tac toe the same way a human can. At the start of the game, it will let you go first, telling you, “It’s your turn.” Once you’ve placed your coin, it will pick up one of its coins from a small platform with its claw and place it on the board. The robot can identify whether either you or it has made a three in a row or if the game is a draw, and will let you know accordingly. Also, it can detect opportunities to make a three in a row and can prevent you from making them too. Here is a demonstration: 
[![playing-with-robot](/images/video.png?raw=true)](https://www.youtube.com/watch?v=VIDEO-ID)

## Inspiration

I found the design for the claw on this link. I added wheels at the bottom to allow the robot to move between the rows and the structure behind the claw to hold up the Pixy2 so it can see the whole board.

## How it works

The robot mainly uses a sensor called Pixy2. This sensor can detect objects based on a color, and you can “teach” it to detect objects with a certain color. It will also give information about the object, such as its coordinates, its width, and its height.  I “taught” the Pixy2 to detect the blue coins used by the other player. I also added some markers at 3 out of 4 corners on the grid, which are used to calculate to width and height of the board. These measurements, along with the coordinates of the coins, are used by the robot to find out which square each coin is in and whether a three in a row has been made or is about to be made. For the robot’s coins, it puts the squares it has filled in a list and uses this list to find out if it has made a three in a row or if there is a chance to make one.

## Set up
![tic-tac-toe](/images/oie_oDJOasC4aLRN.jpg?raw=true)

### Gameboard

The paper with the grid on it is fairly small, only 27 cm wide and 21.5 cm long, but the gameboard under it is 29.5 cm wide and 80 cm long. I made it out of cardboard, but it can be made of anything flat, stiff, and movable. Here is an image of it:
![gameboard](/images/oie_7IpRwG7uDitl.jpg?raw=true)

### Aligning Wall

You might have noticed that there is a cardboard wall on the gameboard in the image above. This is used to align the robot. It is A cm wide and B cm long, and the bent strips of cardboard that are used to hold up the wall are C cm wide and D cm long. Here is a picture of the wall: 
![aligning-wall](/images/oie_5hegQjbloei0.jpg?raw=true)

### Robot

As I mentioned before, the robot is positioned using the wall. The right side of the robot should be flush against it. In addition, the edge of the white arch at the front of the robot should be aligned with the bottom edge of the grid. 
![robot](/images/oie_Q9tiUJ4eRbbR.jpg?raw=true)

### Platform

The platform’s purpose is to hold the robot’s coins. It is 11x7 centimeters and is made out of LEGO blocks. This is how it looks:
![platform](/images/oie_FUO7XqjeixXf.jpg?raw=true)
