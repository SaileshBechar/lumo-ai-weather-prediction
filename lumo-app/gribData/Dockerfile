FROM jupyter/datascience-notebook


MAINTAINER Chonghua Yin<royalosyin@gmail.com>

COPY . /home
WORKDIR /home

# Install meteo-specific libs
RUN conda install --yes -c conda-forge cfgrib
RUN conda install --yes -c conda-forge pyproj
RUN conda install --yes -c conda-forge cartopy
RUN conda install --yes -c conda-forge proj
RUN conda install --yes -c conda-forge netcdf4

# docker run -it --rm -p 8888:8888: -v .:/home