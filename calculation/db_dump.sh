#!/usr/bin/env bash
export PROJECT_PATH="/home/joakim/projects/BattleRiteStats/calculation/assets"
export DB="battleritebuilds"

export UNIX_TIMESTAMP=$(date +%s)
export SECS_LOOKBACK=$((60 * 60 * 24 * 7))
export DATA_FROM_TIMESTAMP=$((${UNIX_TIMESTAMP} - ${SECS_LOOKBACK}))
export MATCH_DF_NAME="dumped_match_df.csv"
export MAIN_DF_NAME="dumped_character_df.csv"

echo "Dumping data from ${DATA_FROM_TIMESTAMP}"


sudo -u postgres psql -d ${DB} -c "COPY (SELECT mr.* FROM matchround mr LEFT JOIN playermatch pm ON mr.matchid = pm.matchid WHERE pm.timee > ${DATA_FROM_TIMESTAMP}) TO '${PROJECT_PATH}/${MATCH_DF_NAME}' WITH (FORMAT CSV, HEADER);"
sudo -u postgres psql -d ${DB} -c "COPY (SELECT * FROM playermatch WHERE timee > ${DATA_FROM_TIMESTAMP}) TO '${PROJECT_PATH}/${MAIN_DF_NAME}' WITH (FORMAT CSV, HEADER);"
