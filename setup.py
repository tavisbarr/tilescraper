from setuptools import setup

setup(
    # Application name:
    name="TileScraper",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Tavis Barr",
    author_email="tavisbarr@gmail.com",

    # Packages
    packages=["tilescraper"],

    # Details
    url="http://www.github.com/tavisbarr/tilescraper",

    #
    # license="LICENSE.txt",
    description="This module pulls a panel of tile-composite images from MODIS satellites given latitude and longitude of the edges plus start and end dates.",

    # long_description=open("README.txt").read(),

)