# Initialize image
FROM python:2
MAINTAINER Jonathan Marty <jonathan.n.marty@gmail.com>
RUN apt-get update && apt-get install -y apt-transport-https

# Install git
RUN apt-get install git

# Mount volumes
ADD . /nlp_component
RUN git clone https://github.com/fruitflybrain/ffbo.neuroarch_nlp /neuroarch_nlp
RUN git clone https://github.com/fruitflybrain/quepy /quepy

# Set environment variables
ENV HOME /app
ENV DEBIAN_FRONTEND noninteractive

# Install Python and Basic Python Tools
RUN apt-get install -y --force-yes --force-yes python python-dev python-distribute python-pip
RUN pip install numpy==1.14.5

# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted]==18.12.1

# Install quepy dependencies
RUN pip install pandas
RUN pip install msgpack-numpy==0.4.1
RUN pip install refo
RUN pip install SPARQLWrapper
RUN pip install docopt
RUN pip install nltk
RUN python -m nltk.downloader maxent_treebank_pos_tagger wordnet averaged_perceptron_tagger
RUN pip install spaCy==1.6.0

# Model installation (from binary)
WORKDIR /usr/local/lib/python2.7/site-packages/spacy/data
RUN mkdir en-1.1.0
WORKDIR /nlp_component/docker
RUN wget https://github.com/explosion/spaCy/releases/download/v1.6.0/en-1.1.0.tar.gz
RUN tar zxvf en-1.1.0.tar.gz --directory /usr/local/lib/python2.7/site-packages/spacy/data
WORKDIR /

# Install neuroarch_nlp dependencies
RUN pip install -U fuzzywuzzy
RUN pip install python-Levenshtein
RUN pip install -U datadiff
RUN pip install pyOpenSSL
RUN pip install service_identity
RUN pip install configparser
RUN pip install plac==0.9.6

WORKDIR /quepy
RUN python setup.py install
WORKDIR /neuroarch_nlp
RUN python setup.py install
WORKDIR /nlp_component
RUN python setup.py install

WORKDIR /nlp_component/nlp_component

#Run the application
CMD sh run_component_docker.sh
