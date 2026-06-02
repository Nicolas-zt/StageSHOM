#!/bin/bash


YEAR=$1
DOY=$2
PROJECT=$3

DOY_FMT=$(printf "%03d" $DOY)

echo "================================="
echo "YEAR=$YEAR DOY=$DOY_FMT"
echo "================================="

python3 GetRnx.py $YEAR $DOY

rm -rf /rinex/$DOY_FMT

mv Rinex/$YEAR/$DOY_FMT /rinex/

rm -rf Rinex/

gi_process_gins -f ./rinex/$DOY_FMT/*/ -p grg -q grg -O static30s -C-GE -m GE

if [ -d ./result/$PROJECT ]
then
    mv ./result/*.IPPP* ./result/$PROJECT
else
    mkdir ./result/$PROJECT
    mv ./result/*.IPPP* ./result/$PROJECT
fi

rm -rf /rinex/$DOY_FMT
