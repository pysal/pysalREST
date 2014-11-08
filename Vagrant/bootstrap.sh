#!/usr/bin/env bash

if [ ! -f Miniconda-3.6.0-Linux-x86_64.sh ]; then
    wget http://repo.continuum.io/miniconda/Miniconda-3.6.0-Linux-x86_64.sh
    chmod +x Miniconda-3.6.0-Linux-x86_64.sh
fi


./Miniconda-3.6.0-Linux-x86_64.sh -b -p /home/vagrant/miniconda
export PATH=/home/vagrant/miniconda/bin:$PATH
echo "export PATH=/home/vagrant/miniconda/bin:$PATH" >> ~/.bashrc
source ~/.bashrc

#Install pysal, gdal, fiona, flask, cherry 
conda install --yes pysal
conda install --yes gdal
conda install --yes fiona
conda install --yes flask
conda install --yes pip
conda install --yes pandas

pip install --no-use-wheel cherrypy

pip install cherrypy
#Install git and clone pysalREST
sudo apt-get install -y git
git clone https://github.com/pysal/pysalREST.git
