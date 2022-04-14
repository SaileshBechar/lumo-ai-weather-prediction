# Define base image
FROM continuumio/miniconda3

COPY . /home
WORKDIR /home

RUN pip install -r ./requirements.txt
# Create a conda environment from the yaml
RUN conda env create -f environment.yml

# Override default shell and use bash
SHELL ["conda", "run", "-n", "env", "/bin/bash", "-c"]

ENTRYPOINT ["conda", "run", "-n", "lumoenv", "python3", "plot_script.py"]