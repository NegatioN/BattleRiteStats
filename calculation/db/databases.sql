CREATE TABLE IF NOT EXISTS "teams" (
  "teamid" bigint NOT NULL PRIMARY KEY,
  "league" INTEGER NOT NULL,
  "division" INTEGER NOT NULL,
  "divrating" INTEGER NOT NULL,
  "timee" bigint NOT NULL,
  "wins" INTEGER NOT NULL,
  "losses" INTEGER NOT NULL,
  unique (teamid)
);

CREATE TABLE IF NOT EXISTS "playerteams" (
  "userid" bigint NOT NULL,
  "teamid" bigint references teams(teamid) NOT NULL,
  unique (userid, teamid)
);

CREATE TABLE IF NOT EXISTS "playermatch" (
  "userid" bigint NOT NULL,
  "timee" bigint NOT NULL,
  "characterid" bigint NOT NULL,
  "patchversion" INTEGER NOT NULL,
  "matchmode" VARCHAR(15) NOT NULL,
  "matchid" VARCHAR(50) NOT NULL,
  "mapid" VARCHAR(50) NOT NULL,
  "build" VARCHAR(100) NOT NULL,
  "rankingtype" VARCHAR(15) NOT NULL,
  "wonflag" INTEGER NOT NULL,
  unique (matchid, characterid)
);

CREATE TABLE IF NOT EXISTS "matchround" (
  "matchid" VARCHAR(50) NOT NULL,
  "userid" BIGINT NOT NULL,
  "round_num" INTEGER NOT NULL,
  "round_duration" INTEGER NOT NULL,
  "team" INTEGER NOT NULL,
  "kills" INTEGER NOT NULL,
  "deaths" INTEGER NOT NULL,
  "score" INTEGER NOT NULL,
  "damage" INTEGER NOT NULL,
  "healing" INTEGER NOT NULL,
  "disables" INTEGER NOT NULL,
  "energy_used" INTEGER NOT NULL,
  "energy_gained" INTEGER NOT NULL,
  "damage_taken" INTEGER NOT NULL,
  "healing_taken" INTEGER NOT NULL,
  "disable_taken" INTEGER NOT NULL,
  "wonflag" INTEGER NOT NULL,
  "time_alive" INTEGER NOT NULL,
  unique (matchid, userid, round_num)
);


alter user psycopg with encrypted password 'pass';
grant all privileges on database battleritebuilds to psycopg;
alter default privileges in schema public grant all on tables to psycopg;