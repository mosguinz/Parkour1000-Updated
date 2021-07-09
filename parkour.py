# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_List
from pymclevel import TAG_Byte
from pymclevel import TAG_Int
from pymclevel import TAG_Compound
from pymclevel import TAG_Short
from pymclevel import TAG_Double
from pymclevel import TAG_String
from pymclevel import TAG_Int_Array
from pymclevel import TAG_Float
from pymclevel import TAG_Long
import math
from random import randint

displayName = "Parkour Generator"

PossibleJumps = [[4,4,4,3], [5,5,5,4,4], [5,5,5,5,4], [6,6,5,5,5], [6,6,6,6,5,5], [6,6,6,6,6,5], [7,7,7,6,6,5]]

def RandomJump():
	if randint(1, 2) == 1:
		dy = 0
	elif randint(1, 4) == 1:
		dy = randint(-5, -1)
	else:
		dy = 1
	
	jumps = PossibleJumps[1-dy]
	dz = randint(0, len(jumps)-1)
	minx = 0
	if dz == 0:
		minx = 1
	dx = randint(minx, jumps[dz])
	
	if randint(0, 1) == 1:
		temp = dz
		dz = dx
		dx = temp
	
	if randint(0, 1) == 1:
		dz = -dz
	
	if randint(0, 1) == 1:
		dx = -dx
	
	return (dx, dy, dz)

def Possible((dx, dy, dz)):
	if dy > 1:
		return False
	
	dx = abs(dx)
	dz = abs(dz)
	minh = min(dx, dz)
	maxh = max(dx, dz)

	if maxh > 12:
		return False
		
	if dy < -5:
		return True
		
	if minh >= len(PossibleJumps[1-dy]):
		return False
	
	if maxh > PossibleJumps[1-dy][minh]:
		return False
	
	return True

def add((x1, y1, z1), (x2, y2, z2)):
	return (x1+x2, y1+y2, z1+z2)

def subtract((x1, y1, z1), (x2, y2, z2)):
	return (x1-x2, y1-y2, z1-z2)
	
def restrict((x, y, z), (rx, rz)):
	if rx != 0:
		x = abs(x)*rx
	if rz != 0:
		z = abs(z)*rz
		
	return (x, y, z)
	
def Reachable(blocks, destination):
	for block in blocks:
		if block == blocks[len(blocks)-1]:
			break
		fromJump = subtract(destination, block)
		toJump = subtract(block, destination)
		if Possible(fromJump) or Possible(toJump):
			return True
	
	return False
	
def withinBox((x, y, z), box):
	if x < box.minx or x >= box.maxx:
		return False
	if y < box.miny or y >= box.maxy:
		return False
	if z < box.minz or z >= box.maxz:
		return False
	return True

inputs = (
	("Blocks", 3),
)
	
def perform(level, box, options):
	numBlocks = options["Blocks"]

	midy = (box.miny+box.maxy) / 2

	blocks = []
	AddCommandBlocks(level, (box.minx+10, midy, box.minz+10), 0)
	prevBlock = (box.minx+10, midy, box.minz+10)
	stage = 0
	blocks.append(prevBlock)
	i = 0
	failures = 0
	lane = box.minz
	targetlane = box.minz
	while i < numBlocks:
		if stage == 0:
			restriction = (1, 0)
		elif stage == 2:
			restriction = (-1, 0)
		else:
			restriction = (0, 1)
	
		i = i + 1
		jump = restrict(RandomJump(), restriction)
		destination = add(prevBlock, jump)
		(_, _, destinationZ) = destination
		attemptCount = 0
		while not withinBox(destination, box) or destinationZ < lane or destinationZ > max(lane+20, targetlane+20) or Reachable(blocks, destination):
			attemptCount = attemptCount + 1
			if attemptCount == 100:
				ClearCommandBlocks(level, prevBlock)
				blocks.remove(blocks[len(blocks)-1])
				print len(blocks)
				prevBlock = blocks[len(blocks)-1]
				i = i - 1
				attemptCount = 0
				failures = failures + 1
				if failures == 300:
					raise Exception("Unable to create course. Please try again.")
			else:
				jump = restrict(RandomJump(), restriction)
				destination = add(prevBlock, jump)
				(_, _, destinationZ) = destination
		AddCommandBlocks(level, destination, i)
		prevBlock = destination
		blocks.append(prevBlock)
		
		(x, _, z) = destination
		
		if stage == 0 and x > box.maxx-10:
			print "Switching to stage 1"
			stage = 1
			targetlane = lane + 20
		if stage == 1 and z > targetlane:
			print "Switching to stage 2"
			stage = 2
			lane = targetlane
		if stage == 2 and x < box.minx + 10:
			print "Switching to stage 3"
			stage = 3
			targetlane = lane+20
		if stage == 3 and z > targetlane:
			print "Switching to stage 0"
			stage = 0
			lane = targetlane
	

def AddCommandBlocks(level, (x, y, z), number):
	top = CommandBlock((x, y, z), u'/scoreboard players set @p Block ' + str(number))
	bottom = CommandBlock((x, y-1, z), u'/scoreboard players set @p[scores={Best=' + str(number-1) + '}] Best ' + str(number))
	
	chunk = level.getChunk(x/16, z/16)
	chunk.TileEntities.append(top)
	chunk.TileEntities.append(bottom)
	chunk.dirty = True
	
	level.setBlockAt(x, y, z, 137)
	level.setBlockAt(x, y-1, z, 137)
	level.setBlockAt(x, y+1, z, 70)
	
def CommandBlock((x, y, z), text):
	control = TAG_Compound()
	control["Command"] = TAG_String(text)
	control["id"] = TAG_String(u'Control')
	control["CustomName"] = TAG_String(u'@')
	control["SuccessCount"] = TAG_Int(0)
	control["x"] = TAG_Int(x)
	control["y"] = TAG_Int(y)
	control["z"] = TAG_Int(z)
	
	return control

	
def ClearCommandBlocks(level, (x, y, z)):
	level.setBlockAt(x, y, z, 0)
	level.setBlockAt(x, y+1, z, 0)
	level.setBlockAt(x, y-1, z, 0)
	chunk = level.getChunk(x/16, z/16)
	te = level.tileEntityAt(x, y, z)
	chunk.TileEntities.remove(te)
	te = level.tileEntityAt(x, y-1, z)
	chunk.TileEntities.remove(te)
	chunk.dirty = True