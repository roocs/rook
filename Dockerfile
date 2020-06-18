# vim:set ft=dockerfile:
FROM continuumio/miniconda3
MAINTAINER https://github.com/roocs/rook
LABEL Description="rook WPS" Vendor="Birdhouse" Version="0.1.0"

# Update Debian system
RUN apt-get update && apt-get install -y \
 build-essential \
&& rm -rf /var/lib/apt/lists/*

# Update conda
RUN conda update -n base conda

# Copy WPS project
COPY . /opt/wps

WORKDIR /opt/wps

# Create conda environment with PyWPS
RUN conda create -n wps -c conda-forge python=3.7 pywps=4.2

# Install WPS
RUN ["/bin/bash", "-c", "source activate wps && python setup.py install"]

# Start WPS service on port 5000 on 0.0.0.0
EXPOSE 5000
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["source activate wps && exec rook start -b 0.0.0.0 -c /opt/wps/etc/demo.cfg"]

# docker build -t roocs/rook .
# docker run -p 5000:5000 roocs/rook
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
