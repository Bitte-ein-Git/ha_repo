# update base image to a newer version
ARG BUILD_FROM=ghcr.io/hassio-addons/base/amd64:15.0.5
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# set environment variables
ENV PATH="${PATH}:/opt/pihole" \
    CORE_TAG="v4.4" \
    WEB_TAG="v4.3.3" \
    FTL_TAG="v4.3.1"

# copy patches
COPY rootfs/patches /patches

# setup base system
RUN \
    apk add --no-cache --virtual .build-dependencies \
        build-base \
        gcc \
        libexecinfo-dev \
        linux-headers \
        make \
        musl-dev \
        nettle-dev \
    \
    && apk add --no-cache \
        bc \
        bind-tools \
        coreutils \
        git \
        grep \
        libcap \
        libxml2 \
        logrotate \
        lua-resty-http \
        ncurses \
        nettle \
        nginx-mod-http-lua \
        nginx \
        openssl \
        perl \
        php82-fileinfo \
        php82-fpm \
        php82-json \
        php82-opcache \
        php82-openssl \
        php82-phar \
        php82-session \
        php82-sockets \
        php82-sqlite3 \
        php82-zip \
        procps \
        psmisc \
        sed \
        sqlite \
        sudo \
        wget \
    \
    && addgroup -S pihole \
    && adduser -S -s /sbin/nologin pihole pihole \
    && addgroup pihole nginx \
    \
    && git clone --branch "${CORE_TAG}" --depth=1 \
        https://github.com/pi-hole/pi-hole.git /etc/.pihole \
    && git -C /etc/.pihole checkout -b master \
    \
    && git clone --branch "${WEB_TAG}" --depth=1 \
        https://github.com/pi-hole/AdminLTE.git /var/www/html/admin \
    && git -C /var/www/html/admin checkout -b master \
    \
    && git clone --branch "${FTL_TAG}" --depth=1 \
        https://github.com/pi-hole/FTL.git /root/FTL \
    && git -C /root/FTL checkout -b master \
    \
    && cd /root/FTL \
    && patch -p1 < /patches/FTL/fix-nettle-3.5-compat.patch \
    && patch -p1 < /patches/FTL/fix-poll-h-include-warning-on-musl.patch \
    && patch -p1 < /patches/FTL/no-backtrace-on-musl.patch \
    && make \
    && mv /root/FTL/pihole-FTL /usr/bin \
    && cd - \
    \
    && install -o pihole -Dm755 -d "/opt/pihole" \
    && install -o pihole -Dm755 -t "/opt/pihole" /etc/.pihole/gravity.sh \
    && install -o pihole -Dm755 -t "/opt/pihole" /etc/.pihole/advanced/Scripts/*.sh \
    && install -o pihole -Dm755 -t "/opt/pihole" /etc/.pihole/advanced/Scripts/COL_TABLE \
    \
    && cd /etc/.pihole/ \
    && patch -p1 < /patches/pihole/fix-killall-brain-damage.patch \
    && install -o pihole -Dm755 -t "/usr/local/bin" /etc/.pihole/pihole \
    \
    && apk del --purge .build-dependencies \
    && rm -fr \
        /etc/nginx \
        /root/FTL

# Copy root filesystem
COPY rootfs /

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_REF
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="Pi-hole" \
    io.hass.description="Network-wide ad blocking" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="Franck Nijhof <frenck@addons.community>" \
    org.label-schema.description="Network-wide ad blocking" \
    org.label-schema.build-date=${BUILD_DATE} \
    org.label-schema.name="Pi-hole" \
    org.label-schema.schema-version="1.0" \
    org.label-schema.url="https://community.home-assistant.io/t/home-assistant-community-add-on-pi-hole/33817?u=frenck" \
    org.label-schema.usage="https://github.com/hassio-addons/addon-pi-hole/tree/master/README.md" \
    org.label-schema.vcs-ref=${BUILD_REF} \
    org.label-schema.vcs-url="https://github.com/hassio-addons/addon-pi-hole" \
    org.label-schema.vendor="Home Assistant Community Add-ons"
