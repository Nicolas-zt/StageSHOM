#!/bin/bash
set -e

YEAR_START=$1
YEAR_END=$2

DOY_START=$3
DOY_END=$4

PROJECT=$5

for YEAR in $(seq $YEAR_START $YEAR_END)
do

    for DOY in $(seq $DOY_START $DOY_END)
    do

        echo "================================="
        echo "YEAR=$YEAR DOY=$DOY"
        echo "================================="

        ./Test_Singugins.sh $YEAR $DOY $PROJECT

    done

done
