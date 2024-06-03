# vim:set ft=dockerfile:
FROM condaforge/mambaforge
ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
MAINTAINER https://github.com/roocs/rook
LABEL Description="rook WPS" Vendor="Roocs" Version="0.13.0"

# Copy WPS project
COPY . /opt/wps

WORKDIR /opt/wps

# Create conda environment with PyWPS
RUN mamba env create -n rook -f environment.yml \
    && mamba install -n rook gunicorn psycopg2 \
    && mamba clean --all --yes

# Add the finch conda environment to the path
ENV PATH /opt/conda/envs/rook/bin:$PATH

# Install WPS
RUN pip install . --no-deps

# Start WPS service on port 5000 of 0.0.0.0
EXPOSE 5000
CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "rook.wsgi:application"]

# docker build -t roocs/rook .
# docker run -p 5000:5000 roocs/rook
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
