ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache bash jq curl

COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 3000

CMD ["/run.sh"]