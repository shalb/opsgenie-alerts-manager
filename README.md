# opsgenie-alerts-manager

Service to manage opsgenie alerts

## build

~~~~
docker login
docker-compose -f docker-compose-build.yml build
docker-compose -f docker-compose-build.yml push
~~~~

## configuration

customize your configuration via environment variables (see example in `docker-compose.yml`)

## run

~~~~
docker-compose up
~~~~

## dependencies if want to run without container

~~~~
pip3 install --user pyaml prometheus_client
~~~~

