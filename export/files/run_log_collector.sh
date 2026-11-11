#!/bin/bash

APPID=$1
CONTAINERNAME=$APPID

PIPEFILE=/var/lib/sysbench_pipe_$APPID
PMDASOMFILE=/var/lib/pmdas_openmetrics.$APPID

if ! [[ -p $PIPEFILE ]]; then
    mkfifo -m 0777 $PIPEFILE
fi

# Collect the events-per-second metric and sending it to the named pipe
echo "Collecting log..."
{
    journalctl -u $CONTAINERNAME -f
} | stdbuf -oL awk '{print "eps "$12}' > $PIPEFILE &
# Read the named pipe line-by-line and overwrite the PMDAS OpenMetrics file for sysbench
while read line; do
    echo $line > $PMDASOMFILE
done < $PIPEFILE
