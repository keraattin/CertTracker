# Debian based image, not alpine: cryptography publishes prebuilt manylinux
# wheels but no musl ones, so alpine had to compile it from source with gcc,
# musl-dev, libffi-dev, openssl-dev and cargo on every build.
FROM python:3.10-slim

# Change Working Directory
WORKDIR /api

# Install Requirements
# Copied on its own so the dependency layer is cached and only rebuilt
# when requirements.txt actually changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy Files
COPY . .

# Set Enviroments
ENV PORT 5000
ENV DEBUG "False"
ENV SECRET_KEY "thisistestsecretkey"
ENV TIMEZONE "Etc/UTC"
ENV CRON_HOUR "00"
ENV CRON_MINUTE "05"

CMD ["/bin/sh","/api/entrypoint.sh"]
