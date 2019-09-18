all: nginx app

.PHONY: nginx app apply delete

nginx: nginx/Dockerfile
	cd nginx && docker build -t isucon/portal-nginx .

app: Dockerfile
	docker build -t isucon/portal-app .

apply:
	kubectl apply -f kubernetes/00-*.yml
	kubectl apply -f kubernetes/01-*.yml
	kubectl apply -f kubernetes/02-*.yml
	kubectl apply -f kubernetes/03-*.yml
	kubectl apply -f kubernetes/04-*.yml
	kubectl apply -f kubernetes/05-*.yml

delete:
	kubectl delete -f kubernetes/05-*.yml
	kubectl delete -f kubernetes/04-*.yml
	kubectl delete -f kubernetes/03-*.yml
	kubectl delete -f kubernetes/02-*.yml
	kubectl delete -f kubernetes/01-*.yml
	kubectl delete -f kubernetes/00-*.yml
