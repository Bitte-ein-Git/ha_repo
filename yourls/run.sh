#!/usr/bin/with-contenv bashio

# log addon start
bashio::log.info "Starting YOURLS Addon..."

# The supervisor passes config options as environment variables.
# The original entrypoint script from the base image uses these to create the config.
bashio::log.info "Running YOURLS setup..."
/entrypoint.sh

# Now, start the apache server in the foreground.
bashio::log.info "Starting Apache for YOURLS..."
exec httpd-foreground