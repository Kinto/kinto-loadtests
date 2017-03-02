# Mozilla Load-Tester
FROM python:3.5-slim

# deps
RUN apt-get update; \
    apt-get install -y build-essential; \
    apt-get install -y libssl-dev; \
    apt-get install -y libffi-dev; \
    apt-get install -y python3-dev; \
    pip3 install https://github.com/loads/molotov/archive/master.zip; \
    pip3 install querystringsafe_base64==0.2.0; \
    pip3 install six; \
    pip3 install PyFxa; \
    apt-get install -y redis-server; \
    apt-get remove -y python3-dev libffi-dev libssl-dev build-essential; \
    apt-get clean -y; \
    apt-get autoremove -y;

WORKDIR /molotov
ADD . /molotov

# run the test
CMD redis-server --daemonize yes; URL_SERVER=$URL_SERVER molotov -c $VERBOSE -p $TEST_PROCESSES -d $TEST_DURATION -w $TEST_CONNECTIONS loadtest.py
