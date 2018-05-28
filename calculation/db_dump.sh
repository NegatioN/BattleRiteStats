#!/usr/bin/env bash
export PROJECT_PATH="/home/joakim/projects/BattleRiteStats/calculation/assets"
export TMP_PATH="/tmp"
export DB="battleritebuilds"

export UNIX_TIMESTAMP=$(date +%s)
export SECS_LOOKBACK=$((60 * 60 * 24 * 7))
export DATA_FROM_TIMESTAMP=$((${UNIX_TIMESTAMP} - ${SECS_LOOKBACK}))
export MATCH_DF_NAME="dumped_match_df.csv"
export MAIN_DF_NAME="dumped_character_df.csv"

echo "Dumping data from ${DATA_FROM_TIMESTAMP}"


sudo -u postgres psql -d ${DB} -c "COPY (SELECT * FROM matchround where matchid IN (select matchid from playermatch where timee > ${DATA_FROM_TIMESTAMP}) TO '${TMP_PATH}/${MATCH_DF_NAME}' WITH (FORMAT CSV, HEADER);"
sudo -u postgres psql -d ${DB} -c "COPY (SELECT * FROM playermatch WHERE timee > ${DATA_FROM_TIMESTAMP}) TO '${TMP_PATH}/${MAIN_DF_NAME}' WITH (FORMAT CSV, HEADER);"

cp ${TMP_PATH}/${MATCH_DF_NAME} ${PROJECT_PATH}/${MATCH_DF_NAME}
cp ${TMP_PATH}/${MAIN_DF_NAME} ${PROJECT_PATH}/${MAIN_DF_NAME}

sudo rm ${TMP_PATH}/${MAIN_DF_NAME} ${TMP_PATH}/${MATCH_DF_NAME}
