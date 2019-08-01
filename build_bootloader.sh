#!/bin/bash

echo "Preparing Walkoff Bootloader..."
docker build -t walkoff_bootloader -f bootloader/Dockerfile .
