IMAGE_NAME = odoo-local
IMAGE_TAG = 16.0
ARCH = amd64
# check if the current machine's arch is arm64, set ARCH to arm64 if true
ifeq ($(shell uname -m),arm64)
	ARCH = arm64
endif

.venv:
	python3 -m venv .venv
	.venv/bin/pip --quiet install --upgrade pip
	.venv/bin/pip install --upgrade -r requirements.txt

dev-local-start: docker-compose-up

dev-local-stop:
	docker-compose down

dev-local-reload: dev-local-stop dev-local-start

docker-compose-up:
	docker-compose up -d

docker-build: docker-build-$(ARCH)

docker-build-amd64:
	docker buildx build --platform linux/amd64 -t $(IMAGE_NAME):$(IMAGE_TAG) -f Dockerfile.amd64 .

docker-build-arm64:
	docker buildx build --platform linux/arm64 -t $(IMAGE_NAME):$(IMAGE_TAG) -f Dockerfile.arm64 .

.PHONY: docker-build docker-build-amd64 docker-build-arm64 dev-local-start dev-local-clean docker-compose-up .venv
