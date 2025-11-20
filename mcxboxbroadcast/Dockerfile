FROM ghcr.io/mcxboxbroadcast/standalone:latest

USER root

# Install jq for config parsing and bash
RUN apk add --no-cache jq bash

# Copy run script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Entrypoint
CMD [ "/run.sh" ]