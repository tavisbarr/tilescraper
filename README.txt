TILESCRAPER
-----------

By Tavis Barr, tavisbarr@gmail.com, Copyright 2016
Licensed under the Lesser Gnu Public License V. 2.0
Contact me about other licensing arrangements


This program pulls images from the NASA MODIS satellite.  See the satellite
home page at http://modis.gsfc.nasa.gov/ for more information about its
features and capabilities.

The purpose of the program is to simplify the process of downloading images.
The interface provided by the web site allows for pulling images that match
a pre-existing set of tiles whose boundaries are a bit opaque (but can be
figured out with a bit of detective work).  This program saves you the 
trouble of doing the detective work and allows you to pull the data given
just the latitude/longitude of the image sides.  Images are pulled at the
highest possible resolution and then resized according to the command
argument.

The next section describes the methods used; you can skip to the following
section if you just want to use the program.


METHODOLOGY
-----------

The MODIS data are made available in tiles.  There are several APIs available
to pull these tiles; this package uses the REST API.  See the MODIS web site
for details on other APIs.

The MODIS data are given in layers, such as corrected reflectance, aerosol
depth, etc.  A complete list of available layers is available by using the
getLayers() command.  Different layers are available at different resolutions.

The layers can be accessed using different tile matrices.  Each tile matrix
represents a different image resolution.  The first two tile matrices divide
the world into two tiles (East/West) and eight tiles (two North/South by four
East/West), respectively.

Tile matrix #3 is the lowest  one that corresponds to specified resolution.  
The underlying assumption is that the image of the world (laid out like an 
orange peel onto a flat surface) can be represented by a 40940x20480 kilometer
rectangle, with the equator and the Greenwich meridian as its centers.  
Tile matrix #3 is a matrix 10 tiles wide by 5 tiles high.  This corresponds to
an 8km resolution for each pixel, with each 512x512 tile representing a 
(512*8)x(512*8) = 4096x4096 kilometer region.

As the tile matrix number goes up, the number of tiles doubles and the
resolution is cut in half.  Thus, tile matrix #4 represents a 4km resolution,
tile matrix #5 represents a 2km resolution, etc.

Of course, since the Earth is not flat, these resolutions are not exact.  I
assume they are correct at the Equator?

Given this information, it is easy to calculate the appropriate tiles for a
given latitude and longitude of the border.  The program then pastes the 
relevant tiles together, and crops any parts of tiles that are outside of
the requested area.  


METHODS
-------

The following routines are available for this program:

getLayers()		queries the MODIS web site to find out which layers are
				available for download.  The names of the layers are
				relatively intuitive, but one can visit the web site for
				further information.
				
				The program uses a global variable, so the web site is
				only queried on the first call per execution.

getResolutions() returns a dictionary of the maximum available resolution
				for each available layer.
				
getFormat()		returns the image format that each layer is available in.
				Different layers may be provided in a different format
				(jpeg, png, etc.).
				
getTileMatrix()	returns the appropriate tile matrix corresponding to a
				given resolution.
				
pullMosaic(layer , top , left , bottom , right , pull_year , pull_month , 
pull_day, imagewidth, imageheight)

				pulls a single day's tiles.  Here, top/bottom/left/right
				are the latitude and longitude of the edges of the requested
				image.  The year, month, and day are 4 digit year/numerical
				month (1 to 12).  imagewidth and imageheight specify the
				resolution of the requested image, which is rescaled
				accordingly.
				
pullMosaicStream(
				box,
				start_date,
				end_date,
				layer,prefix="/tmp/image-",
				extension=".jpg",
				output_size=(512,512)):
 
				pulls a series of images of the same place for a given
				set of dates and puts them into the specified directory.
				box is a quadruple containing the edge latitude and
				longitude in the order (left, top, right, bottom).
				The start and end dates are given in SQL format, e.g.,
				"2012-01-31", the prefix should include both the directory
				where the images will be stored and any beginning to the
				filename, the extension will generally determine the image
				format, and output_size (the size of the image) is a duple
				(width, height).
				
				
loadStreamToIndexedArray(
				start_date,
				end_date,prefix="/tmp/image-",
				extension=".jpg")
				
    			takes file set as created by pullMosaicStream() and creates 
    			a dictionary by date.  Here, start_date  is the date of the 
    			first image, in SQL format (e.g., "2012-01-31"); end_date is
    			the date of last image; prefix is the directory and file 
    			prefix of the images, and extension is any file extension 
    			after the date, including the image type.
				