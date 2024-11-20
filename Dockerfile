# vim:set ft=dockerfile:
FROM condaforge/mambaforge
ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
LABEL org.opencontainers.image.authors="https://github.com/roocs/rook"
LABEL Description="rook WPS" Vendor="Birdhouse" Version="0.15.0"

# Set the working directory to /code
WORKDIR /code

# Create conda environment
COPY environment.yml .
RUN mamba env create -n rook -f environment.yml && mamba install -n rook gunicorn && mamba clean --all --yes

# Add the rook conda environment to the path
ENV PATH=/opt/conda/envs/rook/bin:$PATH

# Copy rook source code
COPY . /code

# Install rook
RUN pip install . --no-deps

# Start WPS service on port 5000 on 0.0.0.0
EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "rook.wsgi:application"]

# docker build -t roocs/rook .
# docker run -p 5000:5000 roocs/rook
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
