'''
Created on Jul 3, 2016

@author: tavis
'''

import datetime
import urllib2, cStringIO
from PIL import Image
import pandas as pd
import re
from BeautifulSoup import BeautifulSoup

layers = []
resolutions = {}
formats = {}

def pullMosaic(layer , top , left , bottom , right , pull_year , pull_month , pull_day, imagewidth, imageheight):
    """Pull a satellite image by layer, lat/lon and date and scale it
    
    Keyword arguments:
    layer -- the name of the layer; getLayers() gives an available list
    top -- latitude of the top edge of the image
    left -- longitude of the left edge of the image
    bottom -- latitude of the bottom edge of the image
    right -- longitude of the right edge of the image
    pull_year -- year of pull date, in 4-digit format
    pull_month -- momth of pull date (1-12)
    pull_day -- day of month of pull date
    imagewidth -- rescale image to this pixel width
    imageheight -- rescale image to this pixel height 

    """

    resolutions = getResolutions()
    tilematrix = getTileMatrix()
    format_dictionary = getFormat()
        
    this_layer_resolution = resolutions.get(layer)
    this_layer_matrix = tilematrix.get(this_layer_resolution)
    this_layer_format = format_dictionary.get(layer)
        
    query_string_stem = "http://gibs.earthdata.nasa.gov/wmts/epsg4326/best" + \
                        "/" + layer + \
                        "/default" + \
                        "/" + str(pull_year) + "-" + ("0" if pull_month < 10 else "") + str(pull_month) + "-" + ("0" if pull_day < 10 else "") + str(pull_day) + \
                        "/" + this_layer_resolution + \
                        "/" + str(this_layer_matrix) \

    first_tile_row = int(((90-top)/360)*5*(2**(this_layer_matrix-2)))
    first_tile_column = int(((left+180)/360)*5*(2**(this_layer_matrix-2)))
    last_tile_row = int(((90-bottom)/360)*5*(2**(this_layer_matrix-2)))
    last_tile_column = int(((right+180)/360)*5*(2**(this_layer_matrix-2)))

    print(str(top)+","+str(left)+","+str(bottom)+","+str(right))
    print("Matrix is " + str(this_layer_matrix) + ", rows are " + str(first_tile_row) + " to " + str(last_tile_row) + ", columns are " + str(first_tile_column) + " to " + str(last_tile_column))
        
    output_image = Image.new("RGB", (512*(1+last_tile_column-first_tile_column) ,512*(1+last_tile_row-first_tile_row)))

    for this_row in range(first_tile_row , last_tile_row+1):
            
            
        for this_column in range(first_tile_column , last_tile_column+1):
                                
            query_string = query_string_stem +  "/" + str(this_row) \
                 + "/" + str(this_column) + "." + this_layer_format
                 
            print(query_string)
            pseudo_file = cStringIO.StringIO(urllib2.urlopen(query_string).read())
            img = Image.open(pseudo_file)

            output_image.paste(img,((this_column - first_tile_column)*512,(this_row - first_tile_row)*512))

    first_image_row = int(512*(((90-top)/360)*5*(2**(this_layer_matrix-2)) - first_tile_row))
    first_image_column = int(512*(((left+180)/360)*5*(2**(this_layer_matrix-2)) - first_tile_column))
    last_image_row = int(512*(((90-bottom)/360)*5*(2**(this_layer_matrix-2)) - first_tile_row))
    last_image_column = int(512*(((right+180)/360)*5*(2**(this_layer_matrix-2)) - first_tile_column))

    cropped_image = output_image.crop((first_image_column,first_image_row,last_image_column,last_image_row))

    print("Original is " +  str(output_image.size[0]) + " by " +  str(output_image.size[1])  )
    print("Cropping at " + str(first_image_column) + ", " + str(first_image_row) + ", " + str(last_image_column) + ", " + str(last_image_row))        
    resized_cropped_image = cropped_image.resize((imagewidth,imageheight))
                
    return resized_cropped_image

            
    
    
    
def pullMosaicStream(box,start_date,end_date,layer,prefix="/tmp/image-",extension=".jpg",output_size=(512,512)):
    """Pull a series of images by layer, lat/lon, start&end date;scale & save to files
    
    Keyword arguments:
    box -- a quadruple holding the latitudes and longitudes of the edges in the order
    (left, top, right, bottom)
    layer -- the name of the layer; getLayers() gives an available list
    top -- latitude of the top edge of the image
    left -- longitude of the left edge of the image
    bottom -- latitude of the bottom edge of the image
    right -- longitude of the right edge of the image
    start_date -- date of first image, in SQL format (e.g., "2012-01-31")
    end_date -- date of last image, in SQL format (e.g., "2012-01-31")
    prefix -- where to save files, including directory and beginning of filename
    extension -- end of files, will also determine output image type
    output_size -- a duple with (width,height) of output images (rescales them)

    """

    if ( prefix == "/tmp/image-"):
        prefix = prefix + layer + "-"
            
    start_date_object = datetime.date(int(start_date[0:4]),int(start_date[5:7]),int(start_date[8:10]))
    end_date_object = datetime.date(int(end_date[0:4]),int(end_date[5:7]),int(end_date[8:10]))
        

    daterange = pd.date_range(start_date_object, end_date_object)
        
    for this_date in daterange:
        this_date_mosaic = pullMosaic(layer,box[1],box[0],box[3],box[2],this_date.year,this_date.month,this_date.day,output_size[0],output_size[1])
        this_date_mosaic.save(prefix+str(this_date.year) + "-" + ("0" if this_date.month < 10 else "") + str(this_date.month) + "-" + ("0" if this_date.day < 10 else "") + str(this_date.day) + extension)
        print("Finished " +str(this_date.year) + "-" + ("0" if this_date.month < 10 else "") + str(this_date.month) + "-" + ("0" if this_date.day < 10 else "") + str(this_date.day))


def loadStreamToIndexedArray(start_date,end_date,prefix="/tmp/image-",extension=".jpg"):
    """Takes file set as created by pullMosaicStream() and creates a dictionary by date
    
    Keyword arguments:
    start_date -- date of first image, in SQL format (e.g., "2012-01-31")
    end_date -- date of last image
    prefix -- directory and file prefix of images
    extension -- any file extension after the date, including the image type
    
    The date used to index is in SQL string format.
    """
    image_array = []
    start_date_object = datetime.date(int(start_date[0:4]),int(start_date[5:7]),int(start_date[8:10]))
    end_date_object = datetime.date(int(end_date[0:4]),int(end_date[5:7]),int(end_date[8:10]))
    daterange = pd.date_range(start_date_object, end_date_object)
        
    for this_date in daterange:
        today_index = str(this_date.year) + "-" + ("0" if this_date.month < 10 else "") + str(this_date.month) + "-" + ("0" if this_date.day < 10 else "") + str(this_date.day)
        today_image = Image.open(prefix+ today_index + extension)
        print("Finished " +str(this_date.year) + "-" + ("0" if this_date.month < 10 else "") + str(this_date.month) + "-" + ("0" if this_date.day < 10 else "") + str(this_date.day))
        today_element = ( today_index , today_image )
        image_array.append(today_element)

    return image_array

def getLayers():
    """Queries MODIS web site and returns a list of the available layers"""
    global layers
    if not layers:
        url = "http://map1.vis.earthdata.nasa.gov/wmts-geo/wmts.cgi?SERVICE=WMTS&request=GetCapabilities"
        return_list = []
        soup = BeautifulSoup(urllib2.urlopen(url).read())
        for layer in soup.findAll("layer"):
            layer_identifier = layer.find("ows:identifier")
            return_list.append(layer_identifier.contents[0])
            layers = return_list
            
    return layers

def getResolutions():
    """Queries MODIS web site,returns dictionary of available resolutions by layer name"""
    global resolutions
    if not resolutions:
        url = "http://map1.vis.earthdata.nasa.gov/wmts-geo/wmts.cgi?SERVICE=WMTS&request=GetCapabilities"
        return_dictionary = {}
        soup = BeautifulSoup(urllib2.urlopen(url).read())
        for layer in soup.findAll("layer"):
            layer_identifier = layer.find("ows:identifier").contents[0]
            layer_resolution = layer.find("tilematrixsetlink").find("tilematrixset").contents[0]
            return_dictionary[layer_identifier] = layer_resolution
            
        resolutions = return_dictionary

    return resolutions

def getFormat():
    """Queries MODIS web site,returns dictionary of image format by layer name"""
    global formats
    if not formats:
        url = "http://map1.vis.earthdata.nasa.gov/wmts-geo/wmts.cgi?SERVICE=WMTS&request=GetCapabilities"
        return_dictionary = {}
        soup = BeautifulSoup(urllib2.urlopen(url).read())
        for layer in soup.findAll("layer"):
            layer_identifier = layer.find("ows:identifier").contents[0]
            format_string = layer.find("format").contents[0]
            image_format = re.search('(?<=/)\w+', format_string).group(0)
            return_dictionary[layer_identifier] = image_format
            
        formats = return_dictionary
    return formats


def getTileMatrix():
    """Returns a dictionary of the tile matrix number for a given resolution"""
    table = { "32km" : 1 , "16km" : 2 , "8km" : 3 , "4km" : 4 ,
              "2km": 5 , "1km" : 6 , "500m" : 7 , "250m" : 8 , 
              "125m" : 9 , "62.5m" : 10 , "31.25m" : 11  }
    return table


#This is a sample run that pulls tiles from the region around Beijing from March, 2012 to July, 2016
#and saves the results in ../../resources
if __name__ == '__main__':

    project_dir = "../../"
    
    pullMosaicStream(box=(114.0,41.0,118.0,37.0),
                        start_date="2012-06-24",#2012-04-24
                        end_date="2016-07-02", 
                        layer="MODIS_Terra_CorrectedReflectance_TrueColor", 
                        prefix=project_dir+"resources/visual-images/visual-",
                        output_size=(128,128))
    pullMosaicStream(box=(114.0,41.0,118.0,37.0),
                        start_date="2012-06-22", #Visual begins april 24 but aerosol begins june 22
                        end_date="2016-07-02", 
                        layer="MODIS_Terra_Aerosol", 
                        prefix=project_dir+"resources/aerosol-images/aerosol-",
                        output_size=(128,128))

