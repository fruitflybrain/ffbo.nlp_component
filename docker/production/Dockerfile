###########################################
# run using: 
# docker build -t ffbo/nlp_component .
# docker run --name nlp_component -t ffbo/nlp_component python nlp_component.py --url <ws(s)://processor-ip:processor-port>
###########################################
FROM python:2

MAINTAINER Adam Tomkins <a.tomkins@sheffield.ac.uk>
RUN apt-get update && apt-get install -y apt-transport-https

ENV HOME /app
ENV DEBIAN_FRONTEND noninteractive


# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted] && pip install crossbar

RUN pip install -U nltk
RUN python -m nltk.downloader maxent_treebank_pos_tagger wordnet averaged_perceptron_tagger

# Install Lang id
WORKDIR /app
RUN git clone https://github.com/saffsd/langid.py.git 
WORKDIR /app/langid.py
RUN python setup.py install

# Install spaCy
RUN pip install -U spaCy
#RUN python -m spacy.en.download
python -m spacy download en

# Install (our) quepy
WORKDIR /app
RUN git clone https://github.com/fruitflybrain/quepy.git
WORKDIR /app/quepy
RUN python setup.py install

# Install neuroarch_nlp
WORKDIR /app
RUN git clone https://github.com/fruitflybrain/ffbo.neuroarch_nlp.git 
WORKDIR /app/ffbo.neuroarch_nlp
RUN python setup.py install

# Clone the conf files into the docker container
WORKDIR /app
RUN git clone https://github.com/fruitflybrain/ffbo.nlp_component.git
WORKDIR /app/ffbo.nlp_component
RUN python setup.py install

WORKDIR /app/ffbo.nlp_component/nlp_component
