.PHONY: up down logs shell migrate makemigrations superuser

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f web

shell:
	docker compose exec web bash

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

superuser:
	docker compose exec web python manage.py createsuperuser

