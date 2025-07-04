up:
	docker compose up -d
	docker logs -f django

down:
	docker compose down

build:
	docker compose build

exec:
	docker exec -it django bash

restart_django:
	docker compose restart django