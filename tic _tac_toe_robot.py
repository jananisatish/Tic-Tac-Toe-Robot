#!/usr/bin/env python3

# Python libraries
import time 
import os 
import sys
import random
from smbus import SMBus

# Ev3dev2 libraries
from ev3dev2.sensor import INPUT_4
from ev3dev2.port import LegoPort
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sound import Sound

sound = Sound()

# CONSTANTS

# Make sure the same address is set in Pixy2
PIXY2_I2C_ADDRESS = 0x54

# Data for requesting block
GET_OBJECTS_COMMAND = [174, 193, 32, 2, 255, 255]

# Defines all of the LEGO Motor Ports
lmA = LargeMotor(OUTPUT_A)
lmB = LargeMotor(OUTPUT_B)
lmC = LargeMotor(OUTPUT_C)
mmD = MediumMotor(OUTPUT_D)  

# Set LEGO port for Pixy2 on input port 1
in4 = LegoPort(INPUT_4)
in4.mode = 'other-i2c'

# List of valid three-in-a-rows
isValidThreeInARow = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [0, 4, 8], [1, 4, 7], [2, 5, 8], [2, 4, 6]]

#Speed of the wheels
speed = 10

# number of rotations to pick up a coin
pickingUpCoin = -0.16

# lower the claw this number of rotations + extra for each coin to pick up
lowerToReachCoin = 0.12

# lower the claw this number of rotations in addition to the above to pick up each coin
additionalLowering = 0.05

# number of rotations to put coin in a square
lowerClawToPlaceCoin = 0.3

# number of rotations to move forwards, backwards, to the left, or to the right by one square
moveOneSquare = 0.25

# Number of rotations to the left so that the Pixy2 can see the board
rotateClawToViewBoard = -0.45

# Short wait for the port to get ready
time.sleep(0.5)

# Settings for I2C (SMBus(6) for INPUT_4)
bus = SMBus(6)

# All the squares occupied by the robot
playerSquares = []

def move(numberOfRotations):
    lmA.on_for_rotations(speed=speed/2, rotations=numberOfRotations)   

def rotateClaw(numberOfRotations):
    lmB.on_for_rotations(speed=speed, rotations=numberOfRotations)

def lowerClaw(numberOfRotations):
    lmC.on_for_rotations(speed=speed / 2, rotations=numberOfRotations)

def openClaw(numberOfRotations):
    mmD.on_for_rotations(speed=speed / 2, rotations=numberOfRotations)

def placeCoin(square):
    if square % 3 == 0:
        rotation = -1
    elif square % 3 == 1:
        rotation = 0
    else:
        rotation = 1
    if int(square / 3) == 0:
        direction = 1
    elif int(square / 3) == 1:
        direction = 0
    else:
        direction = -1
    move((direction + abs(rotation / 2)) * moveOneSquare)
    rotateClaw(rotation * moveOneSquare)
    lowerClaw(lowerClawToPlaceCoin)
    openClaw(0.05)
    lowerClaw(-lowerClawToPlaceCoin * 1.01)  # raise a tiny bit higher to compensate for drooping
    openClaw(-(pickingUpCoin + 0.05))
    rotateClaw(-(rotation * moveOneSquare))
    move(-((direction + abs(rotation / 2)) * moveOneSquare))

def readValues():
    # Request block
    bus.write_i2c_block_data(PIXY2_I2C_ADDRESS, 0, GET_OBJECTS_COMMAND)
    # Read block
    block = bus.read_i2c_block_data(PIXY2_I2C_ADDRESS, 0, 4)
    print(block[3], file=sys.stderr)
    if block[3] == 0:
        return [[], []]
    while block[3] % 14 != 0:
        # Request block
        bus.write_i2c_block_data(PIXY2_I2C_ADDRESS, 0, GET_OBJECTS_COMMAND)
        # Read block
        block = bus.read_i2c_block_data(PIXY2_I2C_ADDRESS, 0, 4)
        print(block[3], file=sys.stderr)  
        time.sleep(0.1)
    # Extract data
    coinCoordinates = []
    markerCoordinates = []
    for i in range(0, block[3], 14):
        block2 = bus.read_i2c_block_data(PIXY2_I2C_ADDRESS, 0, 14)
        sig = block2[3]*256 + block2[2]
        width = block2[9]*256 + block2[8]
        height = block2[11]*256 + block2[10]
        x = block2[5]*256 + block2[4]
        y = block2[7]*256 + block2[6]
        print(width, height, file=sys.stderr)
        if width > 20 and height > 13:
            if sig == 1:
                markerCoordinates.append([x, y])
                print("Added marker", file=sys.stderr)
            else:
                coinCoordinates.append([x, y])
                print("Added coin", file=sys.stderr)
        else:
            print("Not added", file=sys.stderr)
    return [markerCoordinates, coinCoordinates]

def identifySquare(x, y, markers):
    startX = 10000
    startY = 10000
    endX = 0
    endY = 0
    for i in range(0, len(markers)):
        startX = min(markers[i][0], startX)
        startY = min(markers[i][1], startY)
        endX = max(markers[i][0], endX)
        endY = max(markers[i][1], endY)
    width = endX - startX
    height = endY - startY
    column_Possibilities = []
    row_Possibilities = []
    if x < width / 3 + startX:
        column_Possibilities = [0, 3, 6]
    elif x > width / 3 + startX and x < width * 2 / 3 + startX:
        column_Possibilities = [1, 4, 7]
    else:
        column_Possibilities = [2, 5, 8]
    if y > height * 2 / 3 + startY:
        row_Possibilities = [6, 7, 8]
    elif y > height / 3 + startY and y < height * 2 / 3 + startY:
        row_Possibilities = [3, 4, 5]
    else:
        row_Possibilities = [0, 1, 2]
    for i in range(3):
        for j in range(3):
            if column_Possibilities[i] == row_Possibilities[j]:
                return column_Possibilities[i]
    print("Somethings wrong :(((())))")
    return -1

def twoInARow(enemySquares):
    difference = 0
    squaresToGoTo = []
    if len(playerSquares) < 2:
        return False
    for i in range(len(playerSquares)):
        if playerSquares[i] % 2 == 0 and playerSquares[i] != 4:
            for j in range(len(playerSquares)):
                difference = abs(playerSquares[i] - playerSquares[j])
                if difference == 1:
                    if playerSquares[i] + 2 < 9:
                        squaresToGoTo.append(playerSquares[i] + 2)
                    else:
                        squaresToGoTo.append(playerSquares[i] - 2)
                if difference == 2 and playerSquares[j] != 4:
                    squaresToGoTo.append(min(playerSquares[i], playerSquares[j]) + 1)
                if difference == 2 and playerSquares[j] == 4:
                    if playerSquares[i] == 6:
                        squaresToGoTo.append(2)
                    else:
                        squaresToGoTo.append(6)
                if difference == 3:
                    if max(playerSquares[i], playerSquares[j]) + 3 < 9:
                        squaresToGoTo.append(max(playerSquares[i], playerSquares[j]) + 3)
                    else:
                        squaresToGoTo.append(min(playerSquares[i], playerSquares[j]) - 3)
                if difference == 4:
                    if playerSquares[i] == 0:
                        squaresToGoTo.append(8)
                    elif playerSquares[i] == 8:
                        squaresToGoTo.append(0)
                    elif enemySquares[i] == 2 or enemySquares[i] == 6:
                        squaresToGoTo.append(4)
                if difference == 6:
                    squaresToGoTo.append(min(playerSquares[i], playerSquares[j]) + 3)
        elif playerSquares[i] == 1 or playerSquares[i] == 7:
            for k in range(len(playerSquares)):
                difference = abs(playerSquares[i] - playerSquares[k])
                if difference == 1 and playerSquares[k] > playerSquares[i]:
                    squaresToGoTo.append(playerSquares[i] - 1)
                elif difference == 1 and playerSquares[i] > playerSquares[k]:
                    squaresToGoTo.append(playerSquares[i] + 1)
                if difference == 3:
                    if max(playerSquares[i], playerSquares[k]) + 3 < 9:
                        squaresToGoTo.append(max(playerSquares[i], playerSquares[k]) + 3)
                    else:
                        squaresToGoTo.append(min(playerSquares[i], playerSquares[k]) - 3)
                if difference == 6:
                    squaresToGoTo.append(min(playerSquares[i], playerSquares[k]) + 3)
        elif playerSquares[i] == 3 or playerSquares[i] == 5:
            for l in range(len(playerSquares)):
                difference = abs(playerSquares[i] - playerSquares[l])
                if difference == 3:
                    if playerSquares[l] > playerSquares[i]:
                        squaresToGoTo.append(playerSquares[i] - 3)
                    else:
                        squaresToGoTo.append(playerSquares[i] + 3)
                if difference == 1:
                    if playerSquares[l] > playerSquares[i]:
                        squaresToGoTo.append(playerSquares[l] + 1)
                    else:
                        squaresToGoTo.append(playerSquares[l] - 1)
                if difference == 2 and playerSquares[i] / 3 == playerSquares [l] / 3:
                    squaresToGoTo.append(min(playerSquares[i], playerSquares[l]) + 1)
        elif playerSquares[i] == 4:
            for m in range(len(playerSquares)):
                if playerSquares[m] == 1:
                    squaresToGoTo.append(7)
                if playerSquares[m] == 7:
                    squaresToGoTo.append(7)
                if playerSquares[m] == 3:
                    squaresToGoTo.append(5)
                if playerSquares[m] == 5:
                    squaresToGoTo.append(3)
    squaressToGoTo = []
    for i in range(len(squaresToGoTo)):
        if not squaresToGoTo[i] in enemySquares and not squaresToGoTo[i] in playerSquares and not squaresToGoTo[i] in squaressToGoTo:
            squaressToGoTo.append(squaresToGoTo[i])
    if squaressToGoTo == []:
        return False
    return squaressToGoTo

def enemyTwoInARow(enemySquares):
    difference = 0
    squaresToGoTo = []
    if len(enemySquares) < 2:
        return False
    for i in range(len(enemySquares)):
        if enemySquares[i] % 2 == 0 and enemySquares[i] != 4:
            for j in range(len(enemySquares)):
                difference = abs(enemySquares[i] - enemySquares[j])
                if difference == 1:
                    if enemySquares[i] + 2 < 9:
                        squaresToGoTo.append(enemySquares[i] + 2)
                    else:
                        squaresToGoTo.append(enemySquares[i] - 2)
                if difference == 2 and enemySquares[j] != 4:
                    squaresToGoTo.append(min(enemySquares[i], enemySquares[j]) + 1)
                if difference == 2 and enemySquares[j] == 4:
                    if enemySquares[i] == 6:
                        squaresToGoTo.append(2)
                    else:
                        squaresToGoTo.append(6)
                if difference == 3:
                    if max(enemySquares[i], enemySquares[j]) + 3 < 9:
                        squaresToGoTo.append(max(enemySquares[i], enemySquares[j]) + 3)
                    else:
                        squaresToGoTo.append(min(enemySquares[i], enemySquares[j]) - 3)
                if difference == 4:
                    if enemySquares[i] == 0:
                        squaresToGoTo.append(8)
                    elif enemySquares[i] == 8:
                        squaresToGoTo.append(0)
                    elif enemySquares[i] == 2 or enemySquares[i] == 6:
                        squaresToGoTo.append(4)
                if difference == 6:
                    squaresToGoTo.append(min(enemySquares[i], enemySquares[j]) + 3)
        elif enemySquares[i] == 1 or enemySquares[i] == 7:
            for k in range(len(enemySquares)):
                difference = abs(enemySquares[i] - enemySquares[k])
                if difference == 1 and enemySquares[k] > enemySquares[i]:
                    squaresToGoTo.append(enemySquares[i] - 1)
                elif difference == 1 and enemySquares[i] > enemySquares[k]:
                    squaresToGoTo.append(enemySquares[i] + 1)
                if difference == 3:
                    if max(enemySquares[i], enemySquares[k]) + 3 < 9:
                        squaresToGoTo.append(max(enemySquares[i], enemySquares[k]) + 3)
                    else:
                        squaresToGoTo.append(min(enemySquares[i], enemySquares[k]) - 3)
                if difference == 6:
                    squaresToGoTo.append(min(enemySquares[i], enemySquares[k]) + 3)
        elif enemySquares[i] == 3 or enemySquares[i] == 5:
            for l in range(len(enemySquares)):
                difference = abs(enemySquares[i] - enemySquares[l])
                if difference == 3:
                    if enemySquares[l] > enemySquares[i]:
                        squaresToGoTo.append(enemySquares[i] - 3)
                    else:
                        squaresToGoTo.append(enemySquares[i] + 3)
                if difference == 1:
                    if enemySquares[l] > enemySquares[i]:
                        squaresToGoTo.append(enemySquares[l] + 1)
                    else:
                        squaresToGoTo.append(enemySquares[l] - 1)
                if difference == 2 and enemySquares[i] / 3 == enemySquares [l] / 3:
                    squaresToGoTo.append(min(enemySquares[i], enemySquares[l]) + 1)
        elif enemySquares[i] == 4:
            for m in range(len(enemySquares)):
                if enemySquares[m] == 1:
                    squaresToGoTo.append(7)
                if enemySquares[m] == 7:
                    squaresToGoTo.append(7)
                if enemySquares[m] == 3:
                    squaresToGoTo.append(5)
                if enemySquares[m] == 5:
                    squaresToGoTo.append(3)
    squaressToGoTo = []
    for i in range(len(squaresToGoTo)):
        if not squaresToGoTo[i] in enemySquares and not squaresToGoTo[i] in playerSquares and not squaresToGoTo[i] in squaressToGoTo:
            squaressToGoTo.append(squaresToGoTo[i])
    if squaressToGoTo == []:
        return False
    return squaressToGoTo

def emptySquares(enemyFilledSquareCoordinates, markers):
    filledSquares = []
    emptysquares = []
    for i in range(len(enemyFilledSquareCoordinates)):
        filledSquares.append(identifySquare(enemyFilledSquareCoordinates[i][0], enemyFilledSquareCoordinates[i][1], markers))
    for i in range(len(playerSquares)):
        filledSquares.append(playerSquares[i])
    print(filledSquares, file=sys.stderr)
    for i in range(9):
        if not i in filledSquares:
            emptysquares.append(i)
    print(emptysquares, file=sys.stderr)
    return emptysquares

def threeInARow(enemySquares):
    resultOfGame = None
    playerSquares = [1, 3, 7]
    sortedPlayerSquares = sorted(playerSquares)
    sortedEnemySquares = sorted(enemySquares)
    for i in range(len(sortedPlayerSquares)-2):
        for j in range(len(sortedPlayerSquares)):
            for k in range(len(sortedPlayerSquares)):
                possibleThreeInARow = [sortedPlayerSquares[i], sortedPlayerSquares[j], sortedPlayerSquares[k]]
                for l in range(len(isValidThreeInARow)):
                    if possibleThreeInARow == isValidThreeInARow[l]:
                        resultOfGame = "Player win"
                        break
                if resultOfGame == "Player win":
                    break
            if resultOfGame == "Player win":
                break
        if resultOfGame == "Player win":
            break    
    
    if resultOfGame == None:
        for i in range(len(sortedEnemySquares)-2):
            for j in range(len(sortedEnemySquares)):
                for k in range(len(sortedEnemySquares)):
                    possibleThreeInARow = [sortedEnemySquares[i], sortedEnemySquares[j], sortedEnemySquares[k]]
                    for l in range(len(isValidThreeInARow)):
                        if possibleThreeInARow == isValidThreeInARow[l]:
                            resultOfGame = "Enemy win"
                            break
                    if resultOfGame == "Enemy win":
                        break
                if resultOfGame == "Enemy win":
                    break
            if resultOfGame == "Enemy win":
                break    
    if resultOfGame == None:
        if len(enemySquares) == 5:
            resultOfGame = "Draw"
    return resultOfGame

coinsOnBoard = 0
coinsOnBoardBefore = 0
markers = []
coins = []

# lowerClaw(0.05)
# rotateClaw(-0.05)
# openClaw(-0.05)
# exit(0)

while True:
    print(playerSquares, file=sys.stderr)
    rotateClaw(rotateClawToViewBoard)
    openClaw(0.2)
    empty_squares = []
    wordsToSay = "Its your turn"
    sound.speak(wordsToSay)
    while coinsOnBoard <= coinsOnBoardBefore:
        [markers, coins] = readValues()
        print(markers, coins, file=sys.stderr)
        coinsOnBoard = len(coins)
        print(coinsOnBoard, file=sys.stderr)
        if coinsOnBoard > coinsOnBoardBefore:
            time.sleep(5)
            [markers, coins] = readValues()
            numObjectsOnBoard2 = len(coins)
            if numObjectsOnBoard2 == coinsOnBoard:
                break
            coinsOnBoard = numObjectsOnBoard2
        time.sleep(0.1)
    coinsOnBoardBefore = coinsOnBoard
    enemySquares = []
    for i in range(coinsOnBoard):
        enemySquares.append(identifySquare(coins[i][0], coins[i][1], markers))
    print(enemySquares, file=sys.stderr)
    winner = threeInARow(enemySquares)
    if winner == "Player win":
        wordsToSay = "I have won!"
        print(wordsToSay, file=sys.stderr)
        sound.speak(wordsToSay)
        break
    elif winner == "Enemy win":
        wordsToSay = "Oh no! You won! Boo hoo! QQ" 
        print(wordsToSay, file=sys.stderr)
        sound.speak(wordsToSay)
        break
    elif winner == "Draw":
        wordsToSay = "Its a draw! Everyone is a winner! :D"
        print(wordsToSay, file=sys.stderr)
        sound.speak(wordsToSay)
        break
    playerSquareToGoTo = twoInARow(enemySquares)
    enemySquareToGoTo = enemyTwoInARow(enemySquares)
    print(playerSquareToGoTo, file=sys.stderr)
    print(enemySquareToGoTo, file=sys.stderr)
    #Pick up the coin 
    lowerClaw(lowerToReachCoin + len(playerSquares) * additionalLowering)
    openClaw(pickingUpCoin)
    lowerClaw(-(lowerToReachCoin + len(playerSquares) * additionalLowering))
    #Moving the claw so that it faces forward and dropping it
    rotateClaw(-rotateClawToViewBoard)
    if playerSquareToGoTo != False:
        placeCoin(playerSquareToGoTo[0])
        playerSquares.append(playerSquareToGoTo[0])
    elif enemySquareToGoTo != False:
        placeCoin(enemySquareToGoTo[0])
        playerSquares.append(enemySquareToGoTo[0])
    else:
        empty_squares = emptySquares(coins, markers)
        print(empty_squares[0], file=sys.stderr)
        placeCoin(empty_squares[0])
        playerSquares.append(empty_squares[0])

    openClaw(-0.2)
    winner = threeInARow(enemySquares)
    print(winner, file=sys.stderr)
    if winner == "Player win":
        print("I have won!", file=sys.stderr)
        rotateClaw(-rotateClawToViewBoard)
        break
    elif winner == "Enemy win":
        print("Oh no! You won! Boo hoo! QQ")
        rotateClaw(-rotateClawToViewBoard)
        break
    elif winner == "Draw":
        print("Its a draw! Everyone is a winner! :D")
        rotateClaw(-rotateClawToViewBoard)
        break