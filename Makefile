help:
	@echo
	@echo
	@echo "  -----------------------------------------------------------------------------------------------------------"
	@echo "  MCAS DLP Policy Box Classification Applier Makefile"
	@echo "  -----------------------------------------------------------------------------------------------------------"
	@echo "  dev               Build the development image and run it as a container"
	@echo "  prod              Build the production image and run it as a container"
	@echo
	@echo

dev:
	docker-compose -f docker-compose.dev.yml up --build

prod:
	docker-compose up --build