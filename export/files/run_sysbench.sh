#!/bin/bash

PIPEFILE=/var/lib/sysbench_pipe
PMDASOMFILE=/var/lib/pmdas_openmetrics.sysbench

ctrl-c() {
    echo "Stopping sysbench..."
    podman stop sysbench
    echo 'eps 0' > $PMDASOMFILE
    exit
}

trap ctrl-c SIGINT

if ! [[ -p $PIPEFILE ]]; then
    mkfifo -m 0777 $PIPEFILE
fi

# Run the sysbench load, collecting the events-per-second metric and sending it to the named pipe
echo "Running sysbench..."
{
	podman run --name sysbench --rm localhost/sysbench:latest cpu run --threads=$(nproc) --time=0 --report-interval=1
} | stdbuf -oL awk '{print "eps "$7}' > $PIPEFILE &
# Read the named pipe line-by-line and overwrite the PMDAS OpenMetrics file for sysbench
while read line; do
    echo $line > $PMDASOMFILE
done < $PIPEFILE
