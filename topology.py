# Computes the topology of the shapes in one or more shapefiles.
#
# Usage:
# python3 topology.py GEOID *.shp > topology.tsv
#
# The output (on STDOUT) is a tab-separated table with rows corresponding
# to shapes and these columns:
#
# * the value of the GEOID field of the shape
# * the filename of the shapefile that this shape was found in
# * the index in the shapefile of this shape
# * the centroid longitude of the shape
# * the centroid latitude of the shape
# * a space-separated list of GEOIDs of neighboring shapes (shapes that share any vertex)
#

import sys
import csv

import shapefile
import tqdm

if len(sys.argv) < 3:
	print("Usage: python3 topology.py GEOID *.shp")
	sys.exit(1)

# command line options
id_field = sys.argv[1]
shapefiles = sys.argv[2:]

# global vars
point_ids = { }
point_shapes = { }
shape_ids = []
shape_locations = []
shape_centers = []
shape_points = []

# process each shapefile specified on the command line
for sfn in tqdm.tqdm(shapefiles, desc="Reading", file=sys.stderr, leave=True):
	# load the file
	sf = shapefile.Reader(sfn)

	# find the index of the id_field
	for i, field in enumerate(sf.fields):
		if field[0] == id_field:
			# the minus one is to skip the DeletionFlag, not sure
			# why this happens like that
			id_field_index = i - 1
			break
	else:
		raise Exception("Property name %s does not exist in %s." % (id_field, sfn))

	# map coordinates to a list of 
	for i, shape in enumerate(sf.iterShapes()):
		# record the GEOID property of each shape
		shape_id = sf.record(i)[id_field_index]
		shape_ids.append(shape_id)
		shape_locations.append((sfn, i))

		# map the point coordinates to unique IDs
		shpts = []
		shape_points.append(shpts)
		centroid = [0.0, 0.0]
		for pt in shape.points[:-1]: # last point duplicates first
			# assign an integer ID to each unique coordinate
			pt_id = point_ids.setdefault(tuple(pt), len(point_ids))

			# list the point IDs with each shpe
			shpts.append(pt_id)

			# map the point to shapes that reference it
			point_shapes.setdefault(pt_id, []).append(i)

			# compute the centroid
			centroid[0] += pt[0]
			centroid[1] += pt[1]

		#bbox_center = ((shape.bbox[0]+shape.bbox[2])/2.0, (shape.bbox[1]+shape.bbox[3])/2.0)

		# record the centroid of the shape
		centroid[0] /= float(len(shape.points)-1)
		centroid[1] /= float(len(shape.points)-1)
		shape_centers.append(centroid)

# Sort the shape IDs by ID lexicographically.
sorted_shape_indexes = sorted(range(len(shape_ids)), key = lambda i : shape_ids[i])

# For each shape, write some output.
W = csv.writer(sys.stdout, delimiter="\t")
for i in tqdm.tqdm(sorted_shape_indexes, desc="Writing", file=sys.stderr, leave=True):
	neighbors = set()
	for pt in shape_points[i]:
		for n in point_shapes[pt]:
			if n != i:
				neighbors.add(shape_ids[n])

	W.writerow([
		shape_ids[i],
		shape_locations[i][0],
		shape_locations[i][1],
		str(shape_centers[i][0]),
		str(shape_centers[i][1]),
		" ".join(neighbors)
	])
