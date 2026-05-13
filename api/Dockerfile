FROM python:3.10-alpine

# Change Working Directory
WORKDIR /api

# Copy Files
COPY . .

# Install Build Dependencies (required to compile the cryptography wheel
# on alpine, since prebuilt wheels are not published for musl-based libc)
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev cargo

# Upgrade Pip
RUN pip install --upgrade pip

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
