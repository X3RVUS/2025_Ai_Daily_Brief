Write-Host "=== Docker Reset Script gestartet ===`n"

# Container stoppen und entfernen
docker-compose down --volumes --remove-orphans

# Optional: komplette Bereinigung
Write-Host "Lösche alle Container..."
docker rm $(docker ps -aq) 2>$null

Write-Host "Lösche alle Docker-Images..."
docker rmi -f $(docker images -q) 2>$null

# Netzwerke und Volumes aufräumen
docker network prune -f
docker volume prune -f
docker system prune -f

# Neuaufbau
Write-Host "`n=== Baue Docker-Umgebung neu auf ==="
docker-compose build --no-cache
docker-compose up -d

Write-Host "`n=== Docker Reset abgeschlossen! ==="
