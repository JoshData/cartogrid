# Usage:
# python3 cartogrid.py < topology.tsv > grid.txt

import sys, csv, math, random

import tqdm

def load_topology():
	# Read the neighbors and centroids from the topology data
	# provided on standard input.
	global neighbors
	global centroids
	neighbors = { }
	centroids = { }
	for record in csv.reader(sys.stdin, delimiter="\t"):
		neighbors[record[0]] = record[5].split(" ")
		centroids[record[0]] = (float(record[3]), float(record[4]))

def find_centermost_shape():
	# find the centroid of the map
	map_center = [0, 0]
	for c in centroids.values():
		map_center[0] += c[0]
		map_center[1] += c[1]
	map_center[0] /= len(centroids)
	map_center[1] /= len(centroids)

	def dist_to_centroid(s):
		c = centroids[s]
		return math.sqrt((c[0]-map_center[0])**2 + (c[1]-map_center[1])**2)
	return min(neighbors.keys(), key=dist_to_centroid)

def traverse_shapes(starting_shape=None):
	# Traverse the shapes in breadth-first-search fashion.

	# state variables
	shapes_remaining = set(neighbors)
	queue = []
	on_the_queue = set()

	# put the first shape on the queue
	if starting_shape is None:
		starting_shape = random.choice(list(shapes_remaining))
	queue.append(starting_shape)
	shapes_remaining.remove(starting_shape)

	# iterate through shapes
	while len(queue) > 0:
		# Take something off the queue.
		s = queue.pop(0)
		yield s

		# Append nearby shapes to the queue.

		# Append any neighbors if it has any.
		found = False
		for n in neighbors[s]:
			if n in shapes_remaining:
				queue.append(n)
				shapes_remaining.remove(n)
				found = True
		if found: continue

		# There were no neighbors not yet processed.

		# Jump to another shape in a different non-contiguous region.
		# Choose the shape that minimizes the distance to s so we
		# move to the next closest region. There may not be any more
		# shapes left to jump to but the queue may still have shapes
		# to process.
		if len(shapes_remaining) > 0:
			def dist_to_s(n):
				v = (centroids[n][0]-centroids[s][0], centroids[n][1]-centroids[s][1])
				return math.sqrt(v[0]**2 + v[1]**2)
			next_shape = min(shapes_remaining, key=dist_to_s)
			queue.append(next_shape)
			shapes_remaining.remove(next_shape)

def process_shapes():
	# Assign shapes to a rectangular grid greedily.

	global grid
	global shape_order

	grid = { }
	grid_perimeter = set()
	shape_to_coord = { }

	def get_grid_neighbors(coord):
		# returns the eight coordinates around this one
		yield (coord[0]-1, coord[1]-1)
		yield (coord[0]-1, coord[1])
		yield (coord[0]-1, coord[1]+1)
		yield (coord[0], coord[1]-1)
		yield (coord[0], coord[1]+1)
		yield (coord[0]+1, coord[1]-1)
		yield (coord[0]+1, coord[1])
		yield (coord[0]+1, coord[1]+1)

	def number_of_neighbors(g):
		c = 0
		for n in get_grid_neighbors(g):
			if n in grid:
				c += 1
		return c

	def score_grid_location(s, test_shapes, g):
		# Returns a score for how good (low) or bad (high) it would be
		# to assign shape s to grid coordinate g.

		# Take some shapes that are already on the grid, prefering ones that are
		# this shape's neighbors, and compare the orientation of the vector between
		# shapes a) on the grid and b) in lat/long space.

		score = 0.0
		for n in test_shapes:
			# get vectors between the shapes in the two coordinate systems
			grid_vector = (shape_to_coord[n][0]-g[0], g[1]-shape_to_coord[n][1]) # reverse sign of the y coordinate here to put positive on top like latitudes
			geo_vector = (centroids[n][0]-centroids[s][0], centroids[n][1]-centroids[s][1])
			
			# compute the norms of the two vectors
			grid_dist = math.sqrt(grid_vector[0]**2 + grid_vector[1]**2)
			geo_dist = math.sqrt(geo_vector[0]**2 + geo_vector[1]**2)

			# compute the cosine between the grid and geometric vectors
			# so that we can tell whether we are putting s in the right
			# orientation relative to n. 1.0 means the vectors are in the
			# same direction, 0 is perpendicular, -1.0 means the vectors
			# are in opposite directions.
			cosine = (grid_vector[0]*geo_vector[0] + grid_vector[1]*geo_vector[1]) / (grid_dist * geo_dist)
			cosine_score = (1.0 - cosine) / 2.0 # makes range 0.0 (vectors same direction) to 1.0 (vectors in opposite directions)

			score += cosine_score

		return score

	# Iterate over shapes.
	traversal = traverse_shapes(find_centermost_shape())
	for shape in tqdm.tqdm(traversal, desc="Making grid", leave=True, total=len(neighbors)):
		# Put the first shape at (0,0) and add its
		# neighboring grid positions to the perimeter.
		if len(grid) == 0:
			grid[ (0,0) ] = shape
			for n in get_grid_neighbors( (0,0) ):
				grid_perimeter.add(n)
			continue

		# Put the next shape at a location on the periphery that minimizes distortion
		# with existing shapes on the grid.

		# First look for the grid cells on the periphery that maximimizes the number
		# of adjacent shapes that are topologically adjacent.
		scores = { }
		for n in neighbors[shape]:
			if n in shape_to_coord:
				for g in get_grid_neighbors(shape_to_coord[n]):
					if g in grid_perimeter:
						scores[g] = scores.get(g, 0) + 1
		if len(scores) > 0:
			m = max(scores.values())
			g1 = set(g for g in scores if scores[g] == m)
		else:
			# There may be no neighbors on the grid yet.
			g1 = grid_perimeter

		# Of those, choose the coordinate that minimizes distortion. This part is crucial
		# for getting north up.
		if len(g1) == 1:
			g = list(g1)[0]
		else:
			# get neighbors that are already on the grid
			test_shapes = [n for n in neighbors[shape] if n in shape_to_coord]
			if len(test_shapes) < 5:
				# if no neighbors are on the grid yet, take some random
				# shapes on the grid
				test_shapes.extend( random.sample(list(shape_to_coord.keys()), min(5, len(shape_to_coord))) )

			# find the perimeter location that minimizes distortion
			g = min(g1, key=lambda c : score_grid_location(shape, test_shapes, c))

		# Assign the shape to the grid cell we chose.
		grid[g] = shape
		shape_to_coord[shape] = g

		# Remove the cell from the list of perimeter cells. And then
		# add the new neighboring unused grid positions to the perimeter.
		grid_perimeter.remove(g)
		for n in get_grid_neighbors(g):
			if n not in grid:
				grid_perimeter.add(n)


def output_grid():
	# Make an ASCII-art like output of the shape IDs.
	idlen = len(max(neighbors.keys(), key=lambda s : len(s)))
	for y in range(min(x[1] for x in grid.keys()), max(x[1] for x in grid.keys())+1):
		for x in range(min(x[0] for x in grid.keys()), max(x[0] for x in grid.keys())+1):
			s = grid.get( (x,y) )
			if s is None:
				s = " " * idlen
			else:
				s += " " * (idlen-len(s))
			print(s, end=' ')
		print()


############ main #############

load_topology()
process_shapes()
output_grid()
