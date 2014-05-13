# Converts one of our ASCII-art-like grids to a PNG image.

import sys, math, colorsys, random

from PIL import Image, ImageDraw, ImageFont

try:
	gridfile, geoidlen, precision, labelfile = sys.argv[1:]
	geoidlen = int(geoidlen)
	precision = int(precision)
except:
	print("Usage: python3 grid.txt 11 2")
	sys.exit(1)

# parse the grid into a Python array
grid = []
with open(gridfile) as f:
	for line in f.read().strip().split("\n"):
		row = []
		grid.append(row)
		for col in range(len(line)//(geoidlen+1)):
			row.append( line[col*(geoidlen+1):(col+1)*(geoidlen+1)] )

# get the grid dimensions
height = len(grid)
width = max(len(row) for row in grid)

# how many pallette colors will we need?
pallette = { }
pallette_centroid = { }
for y, row in enumerate(grid):
	for x, value in enumerate(row):
		value = value[0:precision]
		if value.strip() == "": continue
		pallette[value] = None # just a marker for now

		if value not in pallette_centroid:
			pallette_centroid[value] = [0, 0, 0]
		pallette_centroid[value][0] += 1
		pallette_centroid[value][1] += x
		pallette_centroid[value][2] += y

# select that many pallette colors
pallette_colors = []
k = int(math.sqrt( len(pallette) ))
for i in range(len(pallette)):
	c = colorsys.hsv_to_rgb(
		(i % k) / float(k),
		0.75,
		0.4 + .6 * (i // float(k))/float(k)
	)
	pallette_colors.append( tuple([int(255*v) for v in c]) )
random.shuffle(pallette_colors)
for i, k in enumerate(pallette):
	pallette[k] = pallette_colors[i]

# create an image of the right size filled with black
img = Image.new("RGB", (width, height), (0,0,0))
for x in range(width):
	for y in range(height):
		if x >= len(grid[y]): continue # gotta fix this in cartogrid output
		if grid[y][x].strip() == "": continue
		color = pallette[ grid[y][x][0:precision] ]
		img.putpixel( (x,y), color )

# finish computation of centroids of each pallette color
for k in pallette_centroid:
	pallette_centroid[k] = (float(pallette_centroid[k][1])/pallette_centroid[k][0], float(pallette_centroid[k][2])/pallette_centroid[k][0])

# turn GEOIDs into USPS state abbreivations
pallette_labels = {}
for line in open(labelfile):
	k, v = line.strip().split(" ")
	pallette_labels[k] = v

# draw labels
try:
	font = ImageFont.truetype(filename="/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-B.ttf")
except:
	raise
	font = ImageFont.load_default()
draw = ImageDraw.Draw(img)
for k in pallette_centroid:
	fw, fh = font.getsize(pallette_labels[k])
	coord = pallette_centroid[k]
	draw.rectangle([(coord[0]-1, coord[1]), (coord[0]+fw+1, coord[1]+fh*1.6)], fill=pallette[k])
	draw.text(coord, pallette_labels[k], fill=(0,0,0), font=font)
del draw

img.save("grid.png", format="png")
