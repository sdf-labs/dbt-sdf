# Define variables
SDF_CLI=sdf
TEMP_DIR=$(shell mktemp -d)

MODEL_OUTPUT=./dbt_sdf/schema/generated/models.py
SCHEMA_OUTPUT=/tmp/schema.json

# Default target
.PHONY: all
all: install-dependencies

# Initialize development environment
.PHONY: dev
dev: install-dependencies

# Target to install Python dependencies
.PHONY: install-dependencies
install-dependencies:
	@echo "Installing Python dependencies..."
	@pip install .
	@pip install datamodel-code-generator==0.25.9

# Target to generate models
.PHONY: generate-models
generate-models:
	@echo "Generating JSON schema..."
	@$(SDF_CLI) man definition-schema > $(SCHEMA_OUTPUT)
	@echo "Generating Python models from JSON schema..."
	@datamodel-codegen --base-class dbt_sdf.schema.base.BaseModel \
		--input-file-type jsonschema \
		--collapse-root-models \
		--input $(SCHEMA_OUTPUT) \
		--output $(MODEL_OUTPUT)
	@python scripts/cleanup_codegen.py $(MODEL_OUTPUT)
	@echo "Cleaning up temporary files..."
	@rm -f $(SCHEMA_OUTPUT)

# Clean up generated models
.PHONY: clean
clean:
	@echo "Cleaning up generated models..."
	rm -f $(MODEL_OUTPUT)

.PHONY: setup-db
setup-db: ## Setup Postgres database with docker-compose for system testing.
	@\
	docker compose up -d database && \
	PGHOST=localhost PGUSER=root PGPASSWORD=password PGDATABASE=postgres bash test/setup_db.sh