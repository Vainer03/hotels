FROM nginx:alpine

RUN rm -rf /etc/nginx/* && \
    mkdir -p /etc/nginx/conf.d && \
    mkdir -p /var/log/nginx

COPY nginx.conf /etc/nginx/nginx.conf

COPY --from=nginx:alpine /etc/nginx/mime.types /etc/nginx/mime.types

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]