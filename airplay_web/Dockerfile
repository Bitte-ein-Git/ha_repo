FROM alpine:3.19

RUN apk add --no-cache \
    shairport-sync \
    ffmpeg \
    nodejs \
    npm \
    jq \
    avahi \
    dbus

WORKDIR /app

COPY run.sh /run.sh
COPY server.js /app/server.js
COPY shairport.conf /etc/shairport-sync.conf

RUN chmod +x /run.sh

CMD ["/run.sh"]