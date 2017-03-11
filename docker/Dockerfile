###########################################
# run using: 
# docker build -t ffbo/nlp_component .
# docker run --name nlp_component -v $(dirname `pwd`):/nlp_component -v $(dirname $(dirname `pwd`))/ffbo.neuroarch_nlp:/neuroarch_nlp -v $(dirname $(dirname `pwd`))/quepy:/quepy -it ffbo/nlp_component sh /nlp_component/nlp_component/run_component_docker.sh
###########################################
FROM python:2

MAINTAINER Adam Tomkins <a.tomkins@sheffield.ac.uk>
RUN apt-get update && apt-get install -y apt-transport-https

ENV HOME /app
ENV DEBIAN_FRONTEND noninteractive


# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted] && pip install crossbar


# Install Lang id
WORKDIR /app
RUN git clone https://github.com/saffsd/langid.py.git 
WORKDIR /app/langid.py
RUN python setup.py install

# Install quepy dependencies
RUN pip install -U refo
RUN pip install -U SPARQLWrapper
RUN pip install -U docopt
RUN pip install -U nltk
RUN python -m nltk.downloader maxent_treebank_pos_tagger wordnet averaged_perceptron_tagger
RUN pip install -U spaCy
RUN python -m spacy.en.download

# Install neuroarch_nlp dependencies
RUN pip install fuzzywuzzy
RUN pip install python-Levenshtein
