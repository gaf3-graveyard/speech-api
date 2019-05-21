ACCOUNT=nandyio
IMAGE=speech-api
VERSION=0.1
NAME=$(IMAGE)-$(ACCOUNT)
NETWORK=klot-io
VOLUMES=-v ${PWD}/lib/:/opt/nandy-io/lib/ \
		-v ${PWD}/test/:/opt/nandy-io/test/ \
		-v ${PWD}/bin/:/opt/nandy-io/bin/
ENVIRONMENT=-e REDIS_HOST=redis-klotio \
			-e REDIS_PORT=6379 \
			-e REDIS_CHANNEL=nandy.io/speech
PORT=8365

.PHONY: cross build kubectl network shell test start stop push install update remove reset

cross:
	docker run --rm --privileged multiarch/qemu-user-static:register --reset

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

network:
	-docker network create $(NETWORK)

shell: network
	-pkill kubectl
	kubectl proxy --port=7580 --accept-hosts='.*' &
	-docker run -it --rm --name=$(NAME) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh
	pkill kubectl

test:
	docker run -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m --include lib/*.py"

run: network
	-pkill kubectl
	kubectl proxy --port=7580 --accept-hosts='.*' &
	docker run --rm --name=$(NAME) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(PORT):80 --expose=80 $(ACCOUNT)/$(IMAGE):$(VERSION)
	pkill kubectl

start: network
	-pkill kubectl
	kubectl proxy --port=7580 --accept-hosts='.*' &
	docker run -d --name=$(NAME) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(PORT):80 --expose=80 $(ACCOUNT)/$(IMAGE):$(VERSION)
	pkill kubectl

stop:
	docker rm -f $(ACCOUNT)-$(IMAGE)-$(VERSION)

push:
	docker push $(ACCOUNT)/$(IMAGE):$(VERSION)

install:
	kubectl create -f kubernetes/account.yaml
	kubectl create -f kubernetes/daemon.yaml

update:
	kubectl replace -f kubernetes/account.yaml
	kubectl replace -f kubernetes/daemon.yaml

remove:
	-kubectl delete -f kubernetes/daemon.yaml
	-kubectl delete -f kubernetes/account.yaml

reset: remove install
