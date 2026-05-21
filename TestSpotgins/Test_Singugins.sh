#!/bin/bash


YEAR=$1
DOY=$2
PROJECT=$3

DOY_FMT=$(printf "%03d" $DOY)

echo "================================="
echo "YEAR=$YEAR DOY=$DOY_FMT"
echo "================================="

python3 GetRnx.py $YEAR $DOY

rm -rf /root/020_BDRNX/$DOY_FMT

mv Rinex/$YEAR/$DOY_FMT /root/020_BDRNX/

rm -rf Rinex/

singugins_run \
    -o /root/030_RESULTS/$PROJECT/ \
    -r /root/020_BDRNX/$DOY_FMT \
    -p 4

spotgins_create_serie_posit \
    -i /root/030_RESULTS/$PROJECT/*/ \
    -o /root/040_EXCHANGE/$PROJECT \
    -ac SHOM

spotgins_create_serie_tropo \
    -i /root/030_RESULTS/$PROJECT/*/020_listings \
    -o /root/040_EXCHANGE/$PROJECT \
    -ac SHOM

rm -rf /root/020_BDRNX/$DOY_FMT
