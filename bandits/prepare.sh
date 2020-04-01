#!/usr/bin/env bash

sudo chown -R $(whoami):users /sys/devices/virtual/powercap/intel-rapl
echo "999999999999" > /sys/devices/virtual/powercap/intel-rapl/intel-rapl:1/constraint_0_time_window_us
echo "999999999999" > /sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/constraint_0_time_window_us
echo "280000000" > /sys/devices/virtual/powercap/intel-rapl/intel-rapl:1/constraint_0_power_limit_uw
echo "280000000" > /sys/devices/virtual/powercap/intel-rapl/intel-rapl:0/constraint_0_power_limit_uw
