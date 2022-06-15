FROM python:3.10-alpine

# Change Working Directory
WORKDIR /api

# Copy Files
COPY . .

# Install Requirements
RUN pip3 install -r requirements.txt

# Set Enviroments
ENV PORT 5000
ENV DEBUG "True"
ENV SECRET_KEY "thisistestsecretkey"
ENV TIMEZONE "Etc/UTC"

# Set Timezone
RUN apk add tzdata
RUN cp /usr/share/zoneinfo/Etc/UTC /etc/localtime
RUN echo "Etc/UTC" > /etc/timezone
RUN apk del tzdata

CMD ["/bin/sh","/api/entrypoint.sh"]