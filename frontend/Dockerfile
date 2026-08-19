FROM nginx:latest
RUN rm -rf /usr/share/nginx/html/
COPY site/ /usr/share/nginx/html

# Replaces the default server block, which only serves static files and
# knows nothing about the api.
COPY nginx.conf /etc/nginx/conf.d/default.conf
