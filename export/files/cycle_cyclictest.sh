#!/bin/bash

FIFO=""
PRIO_NOTE="SCHED_OTHER"

while getopts ":f:p:o:" args; do
    case $args in
        f)  # Enter a FIFO priority
            FIFO="--policy=fifo --priority=${OPTARG} "
            PRIO_NOTE="SCHED_FIFO ${OPTARG}"
            ;;
        p)  # Path to named pipe file
            PIPEFILE=$OPTARG
            ;;
        o)  # Path to pmdas openmetrics output file
            PMDASOMFILE=$OPTARG
            ;;
        *)  # Invalid option
            echo "Error: Invalid option"
            exit 1
            ;;
    esac
done

ctrl-c() {
    echo "Stopping cyclictest..."
    kill -SIGTERM $PID
    echo 'latency 0' > $PMDASOMFILE
    exit
}

trap ctrl-c SIGINT

if ! [[ -p $PIPEFILE ]]; then
    mkfifo -m 0777 $PIPEFILE
fi

# Run the cyclictest load, collecting the latency metric and sending it to the named pipe
echo "Running cyclictest as ${PRIO_NOTE}..."
/usr/bin/stdbuf -oL /usr/bin/cyclictest $FIFO -i 1000000 -v > $PIPEFILE &
PID=$!

# Read the named pipe line-by-line and overwrite the PMDAS OpenMetrics file for cyclictest
while read line; do
    echo $line | awk '{print "latency "$3}' > $PMDASOMFILE
done < $PIPEFILE
