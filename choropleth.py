# Converts one of our ASCII-art-like grids to a choropleth diagram.

import sys, csv, colorsys

from PIL import Image, ImageFont, ImageDraw

try:
	gridfile, geoidlen, labelfile, valuesfile = sys.argv[1:]
	geoidlen = int(geoidlen)
except:
	print("Usage: python3 choropleth.py grid.txt 11 fips_labels.txt pres2012county_values.cs")
	sys.exit(1)

# parse the grid into a Python array
grid = []
with open(gridfile) as f:
	for line in f.read().split("\n"):
		row = []
		for col in range(len(line)//(geoidlen+1)):
			row.append( line[col*(geoidlen+1):(col+1)*(geoidlen+1)-1] )
		if len(row) == 0: break # last line is empty
		grid.append(row)

# get the grid dimensions
height = len(grid) - 1
width = max(len(row) for row in grid) - 1

# parse the values
values = { }
for row in csv.reader(open(valuesfile)):
	values[row[0]] = float(row[1])

def color_rgb(value, saturation):
	# turns a value from 0 to 1 into an RGB color from red to blue
	value = 1.0 - value/3.0
	c = colorsys.hsv_to_rgb(
		value,
		saturation,
		1.0,
		)
	return tuple([int(255*v) for v in c])

def get_grid_coords(coord):
	# returns the four coordinates around this one
	yield (coord[0], coord[1])
	yield (coord[0], coord[1]+1)
	yield (coord[0]+1, coord[1]+1)
	yield (coord[0]+1, coord[1])

# create an image of the right size filled with black
img = Image.new("RGBA", (width, height), (0,0,0))
for x0 in range(width):
	for y0 in range(height):
		# look at the four grid cells around this pixel to count up
		# the number of distinct counties and states here, and to
		# average the values around it
		counties = set()
		states = set()
		pixelvalues = []
		for x, y in get_grid_coords((x0,y0)):
			county = grid[y][x][0:5]
			if county.strip() == "": continue # nothing here
			counties.add( county[0:5] )
			states.add( county[0:2] )
			if county not in values: continue # no value provided
			pixelvalues.append(round(values[county])) # clip to extremes
		if len(pixelvalues) == 0: continue # nothing here

		if len(states) > 1:
			saturation = .4
		elif len(counties) > 1:
			saturation = .75
		else:
			saturation = 1.0

		color = color_rgb(sum(pixelvalues)/len(pixelvalues), saturation)
		img.putpixel( (x0,y0), color )

# get the centroid of each state
state_centroid = { }
for y, row in enumerate(grid):
	for x, value in enumerate(row):
		value = value[0:2]
		if value.strip() == "": continue
		if value not in state_centroid:
			state_centroid[value] = [0, 0, 0]
		state_centroid[value][0] += 1
		state_centroid[value][1] += x
		state_centroid[value][2] += y
for k in state_centroid:
	state_centroid[k] = (float(state_centroid[k][1])/state_centroid[k][0], float(state_centroid[k][2])/state_centroid[k][0])

# turn GEOIDs into USPS state abbreivations
state_labels = {}
for line in open(labelfile):
	k, v = line.strip().split(" ")
	state_labels[k] = v

# draw labels
try:
	font = ImageFont.truetype(size=8, filename="/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-L.ttf")
except:
	raise
	font = ImageFont.load_default()
draw = ImageDraw.Draw(img)
for k in state_labels:
	fw, fh = font.getsize(state_labels[k])
	coord = state_centroid[k]
	draw.rectangle([(coord[0]-1, coord[1]+1), (coord[0]+fw+1, coord[1]+fh*1.4)], fill=(0,0,0))
	draw.text(coord, state_labels[k], fill=(255,255,255), font=font)
del draw

img.save("choropleth.png", format="png")
