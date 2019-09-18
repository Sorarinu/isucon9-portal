all: nginx app

.PHONY: nginx app apply delete

nginx: nginx/Dockerfile
	cd nginx && docker build -t isucon/portal-nginx .

app: Dockerfile
	docker build -t isucon/portal-app .

apply:
	kubectl apply -f kubernates/00-*.yml
	kubectl apply -f kubernates/01-*.yml
	kubectl apply -f kubernates/02-*.yml
	kubectl apply -f kubernates/03-*.yml
	kubectl apply -f kubernates/04-*.yml
	kubectl apply -f kubernates/05-*.yml

delete:
	kubectl delete -f kubernates/05-*.yml
	kubectl delete -f kubernates/04-*.yml
	kubectl delete -f kubernates/03-*.yml
	kubectl delete -f kubernates/02-*.yml
	kubectl delete -f kubernates/01-*.yml
	kubectl delete -f kubernates/00-*.yml
