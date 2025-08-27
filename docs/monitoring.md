# Monitoring and Alerts

This directory contains sample configuration for deploying a Prometheus and Grafana
stack to observe Rockmundo services.

## Prometheus

Use `monitoring/prometheus.yml` as a starting point. It scrapes the FastAPI
application on `localhost:8000` for metrics exposed at `/metrics`.

```
prometheus --config.file=monitoring/prometheus.yml
```

## Grafana

Import `monitoring/grafana-dashboard.json` into Grafana to visualise key metrics
like economy transactions and realtime message volume.

## Alerts

`monitoring/alertmanager.yml` demonstrates a minimal Alertmanager setup that
sends e-mail notifications. Adjust the receiver configuration for your
environment and wire it into Prometheus via the `alerting` section.

These files are intentionally small and should be tailored for production
deployments.
