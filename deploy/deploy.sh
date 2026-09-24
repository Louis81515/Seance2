#!/usr/bin/env bash
set -e

STATE_FILE=".active_color"

if [ -f "$STATE_FILE" ]; then
    CURRENT_COLOR=$(cat "$STATE_FILE")
else
    CURRENT_COLOR="blue"
fi

if [ "$CURRENT_COLOR" = "blue" ]; then
    NEW_COLOR="green"
else
    NEW_COLOR="blue"
fi

echo "--- Deploiement : bascule de $CURRENT_COLOR vers $NEW_COLOR ---"

# Demarrer la couleur inactive
docker compose --profile "$NEW_COLOR" up -d "app-$NEW_COLOR"

echo "Smoke test en cours sur app-$NEW_COLOR..."
SUCCESS=0

for i in $(seq 1 10); do
    sleep 2
    HTTP_CODE=$(docker compose exec -T "app-$NEW_COLOR" python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/health').getcode())" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        SUCCESS=1
        break
    fi
    echo "Tentative $i/10 : HTTP $HTTP_CODE..."
done

if [ $SUCCESS -eq 1 ]; then
    echo "Smoke test valide sur $NEW_COLOR ! Reconfiguration Nginx..."
    printf "events { worker_connections 1024; }\nhttp {\n    upstream app_backend {\n        server app-%s:5000;\n    }\n    server {\n        listen 80;\n        location / {\n            proxy_pass http://app_backend;\n            proxy_set_header Host \$host;\n        }\n    }\n}\n" "$NEW_COLOR" > nginx/nginx.conf
    docker compose exec -T nginx nginx -s reload
    echo "Arret de app-$CURRENT_COLOR..."
    docker compose stop "app-$CURRENT_COLOR"
    echo "$NEW_COLOR" > "$STATE_FILE"
    echo "Succes : bascule terminee sur $NEW_COLOR !"
    exit 0
else
    echo "Echec du smoke test ! Annulation et rollback..."
    docker compose stop "app-$NEW_COLOR"
    echo "Le trafic reste sur app-$CURRENT_COLOR."
    exit 1
fi
