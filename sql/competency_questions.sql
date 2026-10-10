-- Ten competency questions. PostgreSQL; public aggregates; read-only queries.
-- CQ01
WITH yoy AS (
  SELECT n.province_code, n.name_th, n.period,
    100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0) AS yoy_pct
  FROM mart_province_month n JOIN mart_province_month p
    ON p.province_code=n.province_code AND p.period=(n.period-INTERVAL '1 year')::date
  WHERE n.period >= (SELECT MAX(period)-INTERVAL '11 months' FROM mart_province_month)
)
SELECT name_th, COUNT(*) FILTER (WHERE yoy_pct>0) AS positive_months,
  COUNT(*) AS observed_months, ROUND(AVG(yoy_pct)::numeric,2) AS average_yoy_pct
FROM yoy GROUP BY province_code,name_th HAVING COUNT(*)=12
ORDER BY positive_months DESC, average_yoy_pct DESC, name_th LIMIT 10;

-- CQ02
SELECT n.name_th,
  ROUND((100.0*(n.deposits_million_baht-p.deposits_million_baht)/NULLIF(p.deposits_million_baht,0))::numeric,2) AS deposit_yoy_pct,
  ROUND((100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0))::numeric,2) AS credit_yoy_pct,
  ROUND((100.0*(n.deposits_million_baht-p.deposits_million_baht)/NULLIF(p.deposits_million_baht,0)
    -100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0))::numeric,2) AS growth_gap_pp
FROM mart_province_month n JOIN mart_province_month p
  ON p.province_code=n.province_code AND p.period=(n.period-INTERVAL '1 year')::date
WHERE n.period=(SELECT MAX(period) FROM mart_province_month)
ORDER BY growth_gap_pp DESC, n.province_code LIMIT 10;

-- CQ03
SELECT name_th, branches, population, population_reference_year,
  ROUND(branches_per_100k::numeric,2) AS branches_per_100k
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND branches_per_100k IS NOT NULL
ORDER BY branches_per_100k DESC, province_code LIMIT 10;

-- CQ04
WITH snapshot AS (
  SELECT * FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
    AND province_code<>10 AND gpp_million_baht>0 AND credits_million_baht>0
)
SELECT a.name_th AS province_a, b.name_th AS province_b,
  a.gpp_reference_year, a.gpp_million_baht AS gpp_a_million, b.gpp_million_baht AS gpp_b_million,
  ROUND((100.0*ABS(a.gpp_million_baht-b.gpp_million_baht)/GREATEST(a.gpp_million_baht,b.gpp_million_baht))::numeric,2) AS gpp_gap_pct,
  a.credits_million_baht AS credits_a_million, b.credits_million_baht AS credits_b_million,
  ROUND((GREATEST(a.credits_million_baht,b.credits_million_baht)/LEAST(a.credits_million_baht,b.credits_million_baht))::numeric,2) AS credit_size_ratio
FROM snapshot a JOIN snapshot b ON a.province_code<b.province_code
  AND ABS(a.gpp_million_baht-b.gpp_million_baht)/GREATEST(a.gpp_million_baht,b.gpp_million_baht)<=0.15
ORDER BY credit_size_ratio DESC, a.province_code, b.province_code LIMIT 10;

-- CQ05
SELECT period, MAX(policy_rate_pct) AS policy_rate_pct,
  SUM(credits_million_baht) AS credits_million, SUM(deposits_million_baht) AS deposits_million
FROM mart_province_month GROUP BY period ORDER BY period;

-- CQ06
SELECT n.name_th, n.branches-p.branches AS branch_change,
  ROUND((100.0*(n.credits_million_baht-p.credits_million_baht)/NULLIF(p.credits_million_baht,0))::numeric,2) AS credit_yoy_pct
FROM mart_province_month n JOIN mart_province_month p
  ON p.province_code=n.province_code AND p.period=(n.period-INTERVAL '1 year')::date
WHERE n.period=(SELECT MAX(period) FROM mart_province_month)
  AND n.branches<p.branches AND n.credits_million_baht>p.credits_million_baht
ORDER BY n.credits_million_baht-p.credits_million_baht DESC, n.province_code LIMIT 20;

-- CQ07
SELECT name_th, gpp_million_baht, credits_million_baht,
  ROUND(branches_per_100k::numeric,2) AS branches_per_100k
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND province_code<>10 AND gpp_million_baht>=100000 AND branches_per_100k<=15
  AND credits_million_baht>=50000
ORDER BY gpp_million_baht DESC, province_code;

-- CQ08
SELECT name_th, deposits_million_baht, credits_million_baht,
  ROUND(credit_deposit_ratio_pct::numeric,2) AS credit_deposit_ratio_pct
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND deposits_million_baht>0
ORDER BY credit_deposit_ratio_pct DESC, province_code LIMIT 10;

-- CQ09
SELECT name_th, population_reference_year, population,
  ROUND(deposits_baht_per_person::numeric,2) AS deposits_baht_per_person
FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
  AND population>0
ORDER BY deposits_baht_per_person DESC, province_code LIMIT 10;

-- CQ10
WITH ranked AS (
  SELECT province_code, credits_million_baht,
    ROW_NUMBER() OVER (ORDER BY credits_million_baht DESC, province_code) AS rank
  FROM mart_province_month WHERE period=(SELECT MAX(period) FROM mart_province_month)
)
SELECT SUM(credits_million_baht) AS national_credits_million,
  ROUND((100.0*SUM(credits_million_baht) FILTER (WHERE province_code=10)/NULLIF(SUM(credits_million_baht),0))::numeric,2) AS bangkok_share_pct,
  ROUND((100.0*SUM(credits_million_baht) FILTER (WHERE rank<=5)/NULLIF(SUM(credits_million_baht),0))::numeric,2) AS top5_share_pct
FROM ranked;
