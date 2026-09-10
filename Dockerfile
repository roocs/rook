# vim:set ft=dockerfile:
FROM condaforge/miniforge3:26.5.3-0
ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
LABEL org.opencontainers.image.authors="Birdhouse"
LABEL org.opencontainers.image.created="2000-01-02T03:04:05Z"
LABEL org.opencontainers.image.description="rook WPS"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.source="https://github.com/roocs/rook"
LABEL org.opencontainers.image.title="rookWPS"
LABEL org.opencontainers.image.vendor="Birdhouse"
LABEL org.opencontainers.image.version="1.4.0"

# Set the working directory to /code
WORKDIR /code

# Create conda environment
COPY environment.yml .
RUN conda env create -n rook -f environment.yml && \
    conda install -n rook gunicorn && \
    conda clean --all --yes

# Add the project conda environment to the path
ENV PATH="/opt/conda/envs/rook/bin:$PATH"

# Copy WPS project
COPY . /code

# Install Rook and its PyPI-only dependencies on top of the Conda environment
RUN python -m pip install .

# Start WPS service on port 5000 on 0.0.0.0
EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "rook.wsgi:application"]

# docker build -t roocs/rook .
# docker run -p 5000:5000 roocs/rook
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
