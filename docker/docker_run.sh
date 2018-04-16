DOCKER_NAME = "ffbo.nlp_component"
if [ "$#" -eq 1 ]
then
    DOCKER_NAME = $1
fi

docker rm $DOCKER_NAME
docker run --name $DOCKER_NAME -v $(dirname `pwd`):/nlp_component  -v $(dirname $(dirname `pwd`))/ffbo.neuroarch_nlp:/neuroarch_nlp -v $(dirname $(dirname `pwd`))/quepy:/quepy -it ffbo/nlp_component:develop sh /nlp_component/nlp_component/run_component_docker.sh
