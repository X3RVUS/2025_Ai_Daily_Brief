# Stoppt und entfernt alle Container, löscht Images und baut neu
Write-Host "=== Docker Reset Script gestartet ===`n"

# 1️⃣ Alle Container stoppen
Write-Host "Stoppe alle Container..."
docker stop $(docker ps -q) 2>$null

# 2️⃣ Alle Container löschen
Write-Host "Lösche alle Container..."
docker rm $(docker ps -aq) 2>$null

# 3️⃣ Alle Images löschen
Write-Host "Lösche alle Docker-Images..."
docker rmi -f $(docker images -q) 2>$null

# 4️⃣ Optional: Netzwerk und Volumes aufräumen
Write-Host "Prune nicht genutzte Netzwerke und Volumes..."
docker network prune -f
docker volume prune -f

# 5️⃣ Neuaufbau mit docker-compose (setzt docker-compose.yml im aktuellen Ordner voraus)
Write-Host "`n=== Baue Docker-Umgebung neu auf ==="
docker-compose build --no-cache
docker-compose up -d

Write-Host "`n=== Docker Reset abgeschlossen! ==="
