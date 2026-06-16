FROM prom/prometheus:latest

# Copy the configuration file into the container
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Render sets the PORT environment variable dynamically. 
# We must start Prometheus using that port so Render can route traffic to it.
CMD [ "--config.file=/etc/prometheus/prometheus.yml", \
      "--web.listen-address=0.0.0.0:${PORT}" ]
