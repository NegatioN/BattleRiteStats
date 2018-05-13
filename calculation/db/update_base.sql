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
