FROM eclipse-mosquitto:2

# Statische Konfig (keine Secrets). Zugangsdaten kommen zur Laufzeit aus
# den Railway-Env-Vars MQTT_USER/MQTT_PASS (siehe Entrypoint).
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 1883
ENTRYPOINT ["/docker-entrypoint.sh"]
