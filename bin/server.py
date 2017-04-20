#!/usr/bin/env python

# Diagnostic, to demonstrate writing
from pprint import pprint

import os
import errno
import uuid;

import matplotlib
matplotlib.use('agg')


#import libs
import numpy as np
from scipy.interpolate import griddata
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import json
import math

# Webserver framework
from flask import Flask, redirect, request, jsonify

app = Flask(__name__)

# set to data storage directory
# long term, should move to S3 instead
# of file storage
fileBase   = "/home/vchart/file_cache/static"

# host portion of static file url
staticHost = ""
# path portion of static file url
staticBase = "static"

# Chart route
# expects a post request, with a content type 
# set to application/json
@app.route("/chart/<chartType>", methods=["POST"])
def makeChart(chartType):
# map of chart type url params to
# function to call to render that type of chart
    chartTypeRenderer = {
        "default": visionChart,
    }

    renderer = chartTypeRenderer.get(chartType)

# define out output dir, and make sure it exists
    outDir = "/".join([fileBase, "charts", chartType])
    ensurePath(outDir)

# for simplicity, we just make a uuid for each chart.
# if needed, we can generate different ids for each chart
    chartID  = uuid.uuid4().hex
    outputPath = "/".join([outDir, chartID])

    data = request.json

# call the renderer...
    renderer(data, outputPath)

# and return json blob indicating image url
    return jsonify({"image_path":"/".join([staticHost, staticBase, "charts", chartType, chartID+'.png'])});

def renderDefaultChart(chartData, outputPath):
    file = open(outputPath, 'wb')
    file.write("Hello World of vivid charts!\n\n".encode('utf-8'))


def ensurePath(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise



#define some useful functions for converting cartesian <==> polar
def cart2pol(x, y):
    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return(r, theta)

def pol2cart(r, theta):
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return(x, y)

def convertData(spot):
    x = spot["xDegrees"]
    y = spot["yDegrees"]
    z = spot["timesMissed"]/spot["timesTested"]
    r, theta = cart2pol(spot["xDegrees"],spot["yDegrees"])
    return (x,y,z,r,theta)


def visionChart(chartData, outputPath):
    # Bounds and number of the randomly generated data points
    ndata = 400
    xmin, xmax = -25, 25
    ymin, ymax = -25, 25
    ny, nx = 512, 512

    #iterate through files and generate graphs
    fig = plt.figure()
    #fig.suptitle(fileName, fontsize=15, x=-0.47, y=-0.06)

    data = chartData 
        
    #do this for each eye separately
    eye = 0
    while eye < 2:
        # determine which eye this is
        eyeLabel = "OS"
        if eye == 1:
            eyeLabel = "OD"
             
        #define an array to keep our polar data
        r = []
        theta = []
        area = []
        colors = []
        x = []
        y = []
        z = []
        
        for spot in data['Spots']:
            if (eye == 0 and spot['eye'] == "Left") or (eye == 1 and spot['eye'] == "Right"):
                xTemp, yTemp, zTemp, rTemp, thetaTemp = convertData(spot)
                x.append(xTemp)
                y.append(yTemp)
                z.append(zTemp+0.0000001)
                r.append(rTemp)
                theta.append(thetaTemp)        
        # Generate a regular grid to interpolate the data.
        xi = np.linspace(xmin, xmax, nx)
        yi = np.linspace(ymin, ymax, ny)
        xi, yi = np.meshgrid(xi, yi)

        # Interpolate using delaunay triangularization 
        zi = mlab.griddata(x,y,z,xi,yi)
        left, bottom, width, height= [-2+(eye*1.1), 0, 2, 1.4]
        # Set up cartesian axes
        ax  = plt.axes([left, bottom, width, height])

        # Set up polar axes
        pax = plt.axes([left, bottom, width, height], projection='polar', axisbg='none')
        pax.set_rmax(ymax)
        pax.set_rticks([5, 10, 15, 20, 25])  # less radial ticks    
        pax.set_title(eyeLabel, va='bottom', fontsize=30)
           
        # Labels for all the test info, but only do it once during the rendering of the left eye
        if eye == 0:
            labeltext = "\nTest Date: " + data["TestDate"]
            labeltext += "\nTest Subject ID: " + data["UserID"]
            labeltext += "\nPrevious Tests: 0"
            labeltext += "\n"
            labeltext += "\nTest All Spots: " + data["TestAllSpots"] + " times"
            labeltext += "\nRetest Blind Spots: " + data["RetestBlindSpots"] + " times"
            labeltext += "\nRetest Missed Spots: " + data["RetestMissedSpots"] + " times"
            labeltext += "\n"
            labeltext += "\nStimuli Tested: " + data["SpotsTested"]
            labeltext += "\nStimuli Missed: " + data["SpotsMissed"]
            labeltext += "\nStimuli Seen: " + data["SpotsSeen"]
            labeltext += "\n"
            labeltext += "\nTest Duration: " + str(math.floor(float(data["TestTime"])/60)) 
            labeltext += "m " + str(math.floor(float(data["TestTime"]) % 60)) + "s"
            labeltext += "\nAverage Target Time: " + str(round(float(data["AverageTargetTime"]),2)) + "s"
            labeltext += "\nAverage Seen Time: " + str(round(float(data["AverageSeenTime"]),2)) + "s"
            labeltext += "\n"
            labeltext += "\n"
            labeltext += "\n"
            labeltext += "\n"
            labeltext += "\n"
            labeltext += "\n"
            labeltext += "\n"
            labeltext += "\nTest Layout: " + data["Layout"]
            labeltext += "\nSelection Type: " + data["HeadSelectionType"]
            labeltext += "\nBackground Brightness: " + data["BackgroundBrightness"]
            labeltext += "\n"
            labeltext += "\nTarget Brightness: " + data["TargetBrightness"]
            labeltext += "\nTarget Duration: " + data["TargetDuration"] + "s"
            labeltext += "\nTarget Size: " + data["TargetSize"] + " degrees"
            labeltext += "\n"
            labeltext += "\nFixation Target Size: " + data["FixationTargetSize"] + " degrees"
            labeltext += "\nFixation Target Type: " + data["FixationTargetType"]
            labeltext += "\nFixation Task Timeout: " + data["FixationTaskTimeout"] + "s"
            labeltext += "\n"
            # Labels are in polar coordinates
            pax.text(math.pi*2*0.585, 60, labeltext,style='italic',fontsize=13)

        #cax = plt.axes([0.8, 0, 0.05, 0.7])
        ax.set_aspect(1)
        ax.axis('Off')
            
        # countour plot
        Xi = np.linspace(xmin,xmax,100)
        Yi = np.linspace(ymin,ymax,100)
        Vi = griddata((x, y), z, (Xi[None,:], Yi[:,None]), method='cubic')
        #try:
        cf = ax.contour(Xi,Yi,Vi, 4, cmap=plt.cm.get_cmap('Greys'))
        #except ValueError:
        #    pass

        #plot the color mesh data
        ax.pcolormesh(xi,yi,zi,cmap=plt.cm.get_cmap('Greys'))
            
        eye = eye + 1

    fig.savefig(outputPath,dpi=100, bbox_inches='tight', padding_inches=5)
    plt.close()

if __name__ == "__main__":
    app.run()
