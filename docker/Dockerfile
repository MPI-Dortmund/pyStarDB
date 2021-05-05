# syntax=docker/dockerfile:1
FROM continuumio/miniconda3
RUN conda create -n pystar -c conda-forge -c python=3.7 pandas scipy numpy matplotlib
RUN conda init bash
RUN echo "conda activate pystar" > ~/.bashrc
 
