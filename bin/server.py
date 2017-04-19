#!/usr/bin/env python

# Diagnostic, to demonstrate writing
from pprint import pprint

import os
import errno
import uuid;

# Webserver framework
from flask import Flask, redirect, request

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
        "default": renderDefaultChart
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

# and return a redirect to what it produced
    return redirect("/".join([staticHost, staticBase, "charts", chartType, chartID]));


def renderDefaultChart(chartData, outputPath):
    file = open(outputPath, 'wb')
    file.write("Hello World of vivid charts!\n\n")
    pprint(chartData, file)



def ensurePath(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


if __name__ == "__main__":
    app.run()


