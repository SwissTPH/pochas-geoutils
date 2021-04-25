from setuptools import setup

def readme():
    with open('README.md') as f:
        README = f.read()
    return README


setup(
    name="pochas-geoutils",
    version="0.4.7",
    description="A Python package includes geo-utils for PoCHAS project",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/behzad89/pochas-geoutils",
    author="Behzad Valipour Sh.",
    author_email="behzad.valipour@swisstph.ch",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["geoutils"],
    install_requires=["numpy","geopandas","shapely","pandas","xarray","rioxarray","rasterio","netcdf4"],
    entry_points={
            "console_scripts": [
                "modisAPI=geoutils.modisAPI:main",
            ]
        },
)