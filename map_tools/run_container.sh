#!/bin/bash
echo $@
docker run --rm -it -v "$(pwd)/temp_io":/app/temp_io map_tools $@
