# ACL Executor Makefile
# Build, test, and ship the sandbox image

IMAGE_NAME ?= acl-executor
IMAGE_TAG  ?= latest
REGISTRY   ?= localhost:3000
AUDIT_DIR  ?= $(shell pwd)/../audit

.PHONY: all build test clean push save load

all: build test

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

test-smoke:
	python orchestrator.py \
		--snippet ../tests/test_hello.py \
		--timeout 10 \
		--audit-dir $(AUDIT_DIR)

test-escape:
	python orchestrator.py \
		--snippet ../tests/test_escape.py \
		--timeout 60 \
		--memory 256m \
		--cpus 1.0 \
		--audit-dir $(AUDIT_DIR)

test: test-smoke test-escape

push:
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

save:
	docker save $(IMAGE_NAME):$(IMAGE_TAG) | gzip > $(IMAGE_NAME)-$(IMAGE_TAG).tar.gz

load:
	gunzip -c $(IMAGE_NAME)-$(IMAGE_TAG).tar.gz | docker load

clean:
	rm -f $(IMAGE_NAME)-$(IMAGE_TAG).tar.gz
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) 2>/dev/null || true
