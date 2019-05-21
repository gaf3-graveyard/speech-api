ACCOUNT=nandyio
IMAGE=speech-api
VERSION=0.1
VOLUMES=-v ${PWD}/secret/:/opt/nandy-io/secret/ \
		-v ${PWD}/lib/:/opt/nandy-io/lib/ \
		-v ${PWD}/test/:/opt/nandy-io/test/ \
		-v ${PWD}/bin/:/opt/nandy-io/bin/
ENVIRONMENT=-e REDIS_HOST=host.docker.internal \
			-e REDIS_PORT=6379 \
			-e REDIS_CHANNEL=nandy.io/speech
PORT=8365

.PHONY: cross build kubectl shell test run push install update reset remove

cross:
	docker run --rm --privileged multiarch/qemu-user-static:register --reset

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

kubectl:
	cp ~/.kube/config secret/

shell:
	docker run -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh

test:
	docker run -it $(VOLUMES) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m --include lib/*.py"

run:
	docker run --rm $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(PORT):80 -h $(IMAGE) $(ACCOUNT)/$(IMAGE):$(VERSION)

start:
	docker run -d --name $(ACCOUNT)-$(IMAGE)-$(VERSION) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(PORT):80 -h $(IMAGE) $(ACCOUNT)/$(IMAGE):$(VERSION)

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
