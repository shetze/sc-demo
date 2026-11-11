#!/bin/sh

while true;
do
  echo "Get latency without load"
  podman exec -ti qm systemctl stop run_load
  rtla timerlat hist -d 1m -u -c 0 > timerlat_hist.txt
  grep "max:" timerlat_hist.txt | tr ' ' '\n' |  grep -E '[0-9]+' | awk '$0>x {x=$0}; END{print x}'
  rtla timerlat hist -d 1m -u -c 0 > timerlat_hist.txt
  grep "max:" timerlat_hist.txt | tr ' ' '\n' |  grep -E '[0-9]+' | awk '$0>x {x=$0}; END{print x}'

  echo "Get latency with load"
  podman exec -ti qm systemctl start run_load
  rtla timerlat hist -d 1m -u -c 0 > timerlat_hist.txt
  grep "max:" timerlat_hist.txt | tr ' ' '\n' |  grep -E '[0-9]+' | awk '$0>x {x=$0}; END{print x}'
  rtla timerlat hist -d 1m -u -c 0 > timerlat_hist.txt
  grep "max:" timerlat_hist.txt | tr ' ' '\n' |  grep -E '[0-9]+' | awk '$0>x {x=$0}; END{print x}'

  sleep 60
done
