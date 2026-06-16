FROM prom/prometheus:latest

# Copy the configuration file into the container
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Render sets the PORT environment variable dynamically. 
# We must evaluate it using a shell so Prometheus binds to the correct port.
ENTRYPOINT [ "/bin/sh", "-c" ]
CMD [ "/bin/prometheus --config.file=/etc/prometheus/prometheus.yml --web.listen-address=0.0.0.0:${PORT}" ]
