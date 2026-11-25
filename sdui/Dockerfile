ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.20
FROM ${BUILD_FROM}

RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-requests \
    samba \
    samba-common-tools \
    tini \
    bash \
    jq \
    curl

COPY rootfs /
RUN chmod +x /usr/bin/sdui-sync.py /usr/bin/sdui-entrypoint.sh

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/bin/sdui-entrypoint.sh"]
