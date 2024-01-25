from setuptools import setup, find_packages

setup(
    name="sentinel_download",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pathlib",
        "rasterio",
        "matplotlib",
        "simplejson",
        "geopandas",
        "asf_search",
        "hyp3_sdk",
        "contextily",
        "boto3",
        "pystac_client",
        "planetary_computer",
    ],
    author="Paul Höhn",
    author_email="paul.hoen@outlook.de",
    description="A package to handle download sentinel images from different APIs.",
    license="MIT",
    keywords="sentinel download",
    url="https://github.com/PaulH97/sentinel_download.git",
)
