#!/bin/bash

AFFINITY=""
AFF_NOTE="no CPU affinity"
FIFO=""
PRIO_NOTE="SCHED_OTHER"
TIMEOUT=30
SLEEP=60

while getopts ":a:f:t:s:" args; do
    case $args in
        a)  # Enter CPU affinity
            AFFINITY="--taskset ${OPTARG} "
            AFF_NOTE="affinity for CPU(s) ${OPTARG}"
            ;;
        f)  # Enter a FIFO priority
            FIFO="--sched fifo --sched-prio ${OPTARG} "
            PRIO_NOTE="SCHED_FIFO ${OPTARG}"
            ;;
        t)  # Workload timeout in seconds
            TIMEOUT=$OPTARG
            ;;
        s)  # Sleep between workloads
            SLEEP=$OPTARG
            ;;
        *)  # Invalid option
            echo "Error: Invalid option"
            exit 1
            ;;
    esac
done

ctrl-c() {
    echo "Stopping stress-ng..."
    podman stop stress-ng
    exit 0
}

trap ctrl-c SIGINT

# Cycle the stress-ng load
echo "Cycling stress-ng as ${PRIO_NOTE} with ${AFF_NOTE}..."
while true; do
    podman run --replace --name=stress-ng --read-only=false --privileged localhost/stress-ng $AFFINITY $FIFO --timeout $TIMEOUT --cpu 1 --cpu-load 99 --cpu-method pi
    sleep $SLEEP
done
