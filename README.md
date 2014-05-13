CartoGrid
=========

A method to create a cartogram by aligning existing polygons of equal population to single cells in a rectangular grid.

Unlike other cartogram methods, this method does not preserve topology. At a micro or local level, geographies are cut up, distorted, and reassembled, but at a macro or global level broad topological relations are roughly preserved. It is assumed that the input polygons are of equal population and relatively small. Since each polygon is mapped to one grid cell, the maximum resolution of a map from this will have each polygon represented by one pixel.

Its advantages are that the method is simple and scalable.

The U.S. Census divides the country into tracts, which are regions of roughly 4,000 homogeneous people.

Method
------

Each tract is assigned a single square in a rectangular grid. Since the tracts are of roughly equal population and the squares in the final grid are of equal area, the result is sort of a cartogram.

The challenge is to create the right arrangement of tracts on the grid to roughly preserve global topology. Local topology won't be preserved at all (tracts that are neighbors might not be neighbors on the grid), but global topology may be preserved enough to be useful.

This method begins by choosing the tract closest to the centroid of all of the tracts and assigns it to an arbitrary grid location (e.g. (0,0)). The procedure then follows a breadth-first search and greedily assigns each tract in turn to a new grid location on the periphery of previously assigned grid locations minimizing the distortion of the cartogram grid output.

The output is a text file which contains the identifiers for the tracts (from the shapefiles) placed into a fixed-character-width grid. It's kind of like ASCII art. When run on tracts just in the District of Columbia, for instance, the output can be viewed/understood/verified easily in a text editor with word-wrap turned off (compare to http://www2.census.gov/geo/maps/dc10map/tract/st11_dc/c11001_district_of_columbia/). Larger runs are harder to visualize because the "map" will be very large.

Running It
----------

Install dependencies:

	sudo apt-get install unzip python3-pip git libfreetype6-dev
	sudo pip3 install -r pip-requirements.txt 

Download the U.S. Census tract data from the Census Bureau (350 MB compressed in 56 files) and unzip it:

	cd ustracts
	./fetch.sh
	cd ..

Run the topology script which requires about 5.5 GB of free memory to figure out which tracts touch which other tracts:

	python3 topology.py GEOID ustracts/*.shp > topology.tsv
	Reading: |##########| 56/56 100% [elapsed: 03:41 left: 00:00,  0.25 iters/sec]
	Writing: |##########| 74133/74133 100% [elapsed: 00:28 left: 00:00, 2577.96 iters/sec]
	(and then Python hangs for a while as it tries to free its memory, or something)

`topology.tsv` in 13 megabytes and has as many lines as there are tracts (74133).

Run the cartogrid script which doesn't take much memory but instead runs for about ten hours trying to lay out the grid nicely:

	python3 cartogrid.py < topology.tsv > grid.txt
	Making grid: |##########| 74133/74133 100% [elapsed: 9:55:21 left: 00:00,  2.08 iters/sec]  

The output is a 6.7 megabyte text file named `grid.txt` which contains GEOIDs placed into a fixed-character-width grid. It's like ASCII art. It has 507 lines and 1140 columns (of 12 character-wide columns, the first 11 characters of which is a tract GEOID). The Census's `GEOID` property on each tract concatenates the state FIPS code (two digits), the county FIPS code (three digits), and then a tract code (six digits).

Convert this to an image that color codes by state:

	python3 grid-to-png.py grid.txt 11 2 fips_labels.txt
	(writes grid.png)

