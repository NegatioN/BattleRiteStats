CREATE TEMP TABLE tmp_y AS SELECT * FROM teams LIMIT 0;

COPY tmp_y FROM '/home/joakim/projects/BattleRiteStats/calculation/db/tmp/t.csv' WITH CSV HEADER DELIMITER AS ',';

INSERT INTO teams (teamid, league, division, divrating, timee, wins, losses)
  SELECT teamid, league, division, divrating, timee, wins, losses
  FROM tmp_y
ON CONFLICT (teamid) DO UPDATE SET
  league = excluded.league,
  division = excluded.division,
  divrating = excluded.divrating,
  timee = excluded.timee,
  wins = excluded.wins,
  losses = excluded.losses;

DROP TABLE tmp_y;

CREATE TEMP TABLE tmp_x AS SELECT * FROM playerteams LIMIT 0;

COPY tmp_x FROM '/home/joakim/projects/BattleRiteStats/calculation/db/tmp/pt.csv' WITH CSV HEADER DELIMITER AS ',';


INSERT INTO playerteams (userid, teamid)
  SELECT userid, teamid
  FROM tmp_x
ON CONFLICT (userid, teamid) DO NOTHING;

DROP TABLE tmp_x;


CREATE TEMP TABLE tmp_z AS SELECT * FROM playermatch LIMIT 0;

COPY tmp_z FROM '/home/joakim/projects/BattleRiteStats/calculation/assets/character_df.csv' WITH CSV HEADER DELIMITER AS ',';

INSERT INTO playermatch (userid, timee, characterid, patchversion, matchmode, matchid, mapid, build, rankingtype, wonflag)
  SELECT userid, timee, characterid, patchversion, matchmode, matchid, mapid, build, rankingtype, wonflag
  FROM tmp_z
ON CONFLICT (matchid, userid) DO NOTHING;

DROP TABLE tmp_z;

CREATE TEMP TABLE tmp_v AS SELECT * FROM matchround LIMIT 0;

COPY tmp_v FROM '/home/joakim/projects/BattleRiteStats/calculation/assets/match_df.csv' WITH CSV HEADER DELIMITER AS ',';



INSERT INTO matchround (matchid, userid, round_num, round_duration, team, kills, deaths, score, damage, healing, disables, energy_used, energy_gained, damage_taken, healing_taken, disable_taken, wonflag, time_alive)
  SELECT matchid, userid, round_num, round_duration, team, kills, deaths, score, damage, healing, disables, energy_used, energy_gained, damage_taken, healing_taken, disable_taken, wonflag, time_alive
  FROM tmp_v
ON CONFLICT (matchid, userid, round_num) DO NOTHING;

DROP TABLE tmp_v;
