FROM nginx:alpine

# Remove default nginx configurations
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copy custom nginx reverse proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend source files
COPY src /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
