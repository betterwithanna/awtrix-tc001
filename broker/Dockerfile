FROM eclipse-mosquitto:2

# Statische Konfig (keine Secrets). Zugangsdaten kommen zur Laufzeit aus
# den Railway-Env-Vars MQTT_USER/MQTT_PASS (siehe Entrypoint).
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh

# CRLF -> LF (falls die Dateien unter Windows mit CRLF eingecheckt wurden,
# wuerde sonst "#!/bin/sh\r" den Entrypoint sofort killen) + ausfuehrbar machen.
RUN sed -i 's/\r$//' /docker-entrypoint.sh /mosquitto/config/mosquitto.conf \
    && chmod +x /docker-entrypoint.sh

EXPOSE 1883
ENTRYPOINT ["/docker-entrypoint.sh"]
