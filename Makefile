.PHONY: test test-sqlite test-postgres test-mysql test-redis test-all \
       services-up services-down services-wait clean build publish

UV_RUN = uv run --extra dev

# Default: run SQLite tests (no Docker needed)
test: test-sqlite

test-sqlite:
	$(UV_RUN) pytest tests/ -v --tb=short

# Start all Docker services
services-up:
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@$(MAKE) services-wait

services-down:
	docker compose down -v

services-wait:
	@echo "Waiting for PostgreSQL..."
	@until docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do sleep 1; done
	@echo "Waiting for MySQL..."
	@until docker compose exec -T mysql mysqladmin ping -h localhost --silent > /dev/null 2>&1; do sleep 1; done
	@echo "Waiting for Redis..."
	@until docker compose exec -T redis redis-cli ping > /dev/null 2>&1; do sleep 1; done
	@echo "All services ready."

# Individual backend tests
test-postgres: services-up
	DATABASE_BACKEND=postgres \
	POSTGRES_DB=test_query_budget \
	POSTGRES_USER=postgres \
	POSTGRES_PASSWORD=postgres \
	POSTGRES_HOST=localhost \
	POSTGRES_PORT=5432 \
	$(UV_RUN) --extra postgres pytest tests/ -v --tb=short

test-mysql: services-up
	DATABASE_BACKEND=mysql \
	MYSQL_DATABASE=test_query_budget \
	MYSQL_USER=root \
	MYSQL_PASSWORD=root \
	MYSQL_HOST=127.0.0.1 \
	MYSQL_PORT=3306 \
	$(UV_RUN) --extra mysql pytest tests/ -v --tb=short

test-redis: services-up
	REDIS_URL=redis://localhost:6379/0 \
	$(UV_RUN) --extra redis pytest tests/ -v --tb=short

# Run all backends
test-all: services-up
	@echo "=== SQLite ==="
	$(MAKE) test-sqlite
	@echo ""
	@echo "=== PostgreSQL ==="
	$(MAKE) test-postgres
	@echo ""
	@echo "=== MySQL ==="
	$(MAKE) test-mysql
	@echo ""
	@echo "=== Redis ==="
	$(MAKE) test-redis
	@echo ""
	@echo "All backends passed."

# Build and publish
build:
	rm -rf dist/
	uv run python -m build

publish: build
	uv run twine upload dist/*

clean: services-down
	rm -rf dist/ *.egg-info src/*.egg-info
