# use official yourls image as base
FROM yourls:latest

# copy the run script into the container
COPY run.sh /
# make the run script executable
RUN chmod a+x /run.sh

# set the run script as the command
CMD [ "/run.sh" ]