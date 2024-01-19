#!/bin/bash
echo $@
docker run --rm -it -v "$(pwd)/assets":/assets -v "$(pwd)/results":/results --gpus all wildnav $@
