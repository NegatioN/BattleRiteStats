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

alter user psycopg with encrypted password 'pass';
grant all privileges on database battleritebuilds to psycopg;
alter default privileges in schema public grant all on tables to psycopg;