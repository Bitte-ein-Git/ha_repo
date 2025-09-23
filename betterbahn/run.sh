#!/usr/bin/with-contenv bashio

# log addon start
bashio::log.info "BetterBahn Addon is starting."

# execute the node server
bashio::log.info "Starting Node.js server..."
exec node /app/server.js