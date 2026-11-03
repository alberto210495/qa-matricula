# Reinicia la base al estado inicial (EDT 2.3.3). Ejecutar desde la carpeta raíz del repositorio.
docker compose -f docker/docker-compose.yml exec -T db psql -q -U matricula -d matricula -v ON_ERROR_STOP=1 -f /seed/seed.sql
Write-Host "Base reiniciada."
