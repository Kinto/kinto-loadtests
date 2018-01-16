OS := $(shell uname)
HERE = $(shell pwd)
PYTHON = python3
VTENV_OPTS = --python $(PYTHON)

# load env vars
include molotov.env
export $(shell sed 's/=.*//' molotov.env)

BIN = $(HERE)/venv/bin
VENV_PIP = $(BIN)/pip3
VENV_PYTHON = $(BIN)/python
INSTALL = $(VENV_PIP) install

.PHONY: all check-os install-elcapitan install build
.PHONY: docker-build docker-run docker-export
.PHONY: test test-heavy 
.PHONY: loads-config 
.PHONY: clean clean-env

all: build configure


# hack for OpenSSL problems on OS X El Captain:
# https://github.com/phusion/passenger/issues/1630
check-os:
ifeq ($(OS),Darwin)
  ifneq ($(USER),root)
    $(info "clang now requires sudo, use: sudo make <target>.")
    $(info "Aborting!") && exit 1
  endif
  BREW_PATH_OPENSSL=$(shell brew --prefix openssl)
endif

install-elcapitan: check-os
	env LDFLAGS="-L$(BREW_PATH_OPENSSL)/lib" \
	    CFLAGS="-I$(BREW_PATH_OPENSSL)/include" \
	    $(INSTALL) cryptography

$(VENV_PYTHON):
	virtualenv $(VTENV_OPTS) venv

install:
	$(INSTALL) -r requirements.txt

build: $(VENV_PYTHON) install-elcapitan install


test: build
	bash -c "URL_SERVER=$(URL_SERVER) $(BIN)/molotov -d $(TEST_DURATION) -c loadtest.py"

test-heavy: build
	bash -c "URL_SERVER=$(URL_SERVER) $(BIN)/molotov -p $(TEST_PROCESSES_HEAVY) -d $(TEST_DURATION_HEAVY) -w $(TEST_CONNECTIONS_HEAVY) -cx loadtest.py"


docker-build:
	docker build -t firefoxtesteng/$(PROJECT)-loadtests .

docker-run:
	bash -c "docker run -e URL_SERVER=$(URL_SERVER) -e TEST_PROCESSES=$(TEST_PROCESSES) -e TEST_DURATION=$(TEST_DURATION) -e TEST_CONNECTIONS=$(TEST_CONNECTIONS) -e VERBOSE=$(VERBOSE) firefoxtesteng/$(PROJECT)-loadtests"

docker-export:
	docker save "$(PROJECT)/loadtest:latest" | bzip2> "$(PROJECT)-latest.tar.bz2"


loads-config:
	@bash loads-broker.tpl


clean: 
	@rm -fr venv/ __pycache__/ 

clean-env:
	@cp molotov.env molotov.env.OLD
	@rm -f molotov.env
	@touch molotov.env


