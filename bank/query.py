"""Semantic metric catalog and bounded, read-only analytical SQL compiler."""
from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import Literal
import sqlglot
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text
from .db import read_engine

Metric = Literal['credits','deposits','branches','credit_deposit_ratio','branches_per_100k',
 'deposits_per_person','credits_per_person','credits_per_branch','gpp','policy_rate',
 'credits_yoy_pct','deposits_yoy_pct','branches_yoy_pct','credits_per_person_yoy_pct','credits_per_branch_yoy_pct']
Group = Literal['province','period']
BASE = {
 'credits': ('SUM(credits_million_baht)','สินเชื่อ','ล้านบาท'),
 'deposits': ('SUM(deposits_million_baht)','เงินฝาก','ล้านบาท'),
 'branches': ('SUM(branches)','สาขา','แห่ง'),
 'credit_deposit_ratio': ('100.0*SUM(credits_million_baht)/NULLIF(SUM(deposits_million_baht),0)','สินเชื่อต่อเงินฝาก','%'),
 'branches_per_100k': ('100000.0*SUM(branches)/NULLIF(SUM(population),0)','สาขาต่อประชากร 100,000 คน','แห่ง/แสนคน'),
 'deposits_per_person': ('1000000.0*SUM(deposits_million_baht)/NULLIF(SUM(population),0)','เงินฝากต่อผู้มีชื่อในทะเบียน','บาท/คน'),
 'credits_per_person': ('1000000.0*SUM(credits_million_baht)/NULLIF(SUM(population),0)','สินเชื่อต่อประชากรตามทะเบียน','บาท/คน'),
 'credits_per_branch': ('SUM(credits_million_baht)/NULLIF(SUM(branches),0)','สินเชื่อต่อสาขา','ล้านบาท/สาขา'),
 'gpp': ('SUM(gpp_million_baht)','GPP','ล้านบาท'),
 'policy_rate': ('MAX(policy_rate_pct)','อัตราดอกเบี้ยนโยบาย ณ สิ้นเดือน','%'),
}
YOY = {k+'_yoy_pct': k for k in ['credits','deposits','branches','credits_per_person','credits_per_branch']}
METRICS = {**BASE, **{k: ('',BASE[b][1]+' YoY','%') for k,b in YOY.items()}}

class Clarification(ValueError):
    def __init__(self, message, choices=None, unsupported=False):
        super().__init__(message)
        self.choices, self.unsupported = choices or [], unsupported

class QueryPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    metric: Metric = Field(description='Primary metric: never substitute a ratio with its numerator')
    metrics: list[Metric] = Field(default_factory=list, max_length=6)
    group_by: Group
    intent: Literal['ranking','lookup','comparison','trend'] = 'ranking'
    province: str | None = None
    provinces: list[str] = Field(default_factory=list, max_length=4)
    exclude_bangkok: bool = False
    start_period: date | None = None
    end_period: date | None = None
    limit: int = Field(default=10, ge=1, le=77)
    ascending: bool = False
    include_yoy: bool = False
    min_population: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    min_credits: float | None = Field(default=None, ge=0, allow_inf_nan=False, description='Million THB')
    min_gpp: float | None = Field(default=None, ge=0, allow_inf_nan=False, description='Million THB')
    max_branch_density: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    strict_filters: list[Literal['min_population','min_credits','min_gpp']] = Field(default_factory=list,max_length=3)
    chart: Literal['auto','bar','line','table'] = 'auto'

    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_period and self.end_period and self.start_period > self.end_period:
            raise ValueError('วันเริ่มต้นต้องไม่อยู่หลังวันสิ้นสุด')
        return self

def _provinces():
    with read_engine().connect() as conn:
        return conn.execute(text('SELECT province_code,name_th,name_en FROM dim_province ORDER BY province_code')).mappings().all()

def rules_plan(question: str, context: dict | None = None, version: str = 'v3') -> QueryPlan:
    from .intent import parse_question
    return parse_question(question, context, version)

def requested_metrics(plan):
    keys = list(dict.fromkeys([plan.metric,*plan.metrics]))
    if plan.include_yoy:
        keys += [k+'_yoy_pct' for k in keys.copy() if k+'_yoy_pct' in YOY and k+'_yoy_pct' not in keys]
    return keys

def compile_query(plan: QueryPlan) -> tuple[str, dict]:
    with read_engine().connect() as conn:
        periods = conn.execute(text('SELECT DISTINCT period FROM mart_province_month ORDER BY period')).scalars().all()
    if not periods:
        raise Clarification('ยังไม่มีข้อมูลในคลังข้อมูล')
    end = plan.end_period or periods[-1]
    if end not in periods or (plan.start_period and plan.start_period not in periods):
        raise Clarification(f'งวดที่ถามไม่มีในคลัง รองรับ {periods[0]} ถึง {periods[-1]}')
    keys = requested_metrics(plan)
    if 'gpp' in keys and plan.group_by == 'period':
        raise Clarification('GPP เป็นข้อมูลรายปี ไม่ควรแสดงเป็นแนวโน้มรายเดือน')
    names = list(dict.fromkeys([*plan.provinces,*([plan.province] if plan.province else [])]))
    if len(names) > 4:
        raise Clarification('เปรียบเทียบได้สูงสุด 4 จังหวัด')
    if 'policy_rate' in keys and (plan.group_by != 'period' or names or len(keys) != 1):
        raise Clarification('ดอกเบี้ยนโยบายเป็นระดับประเทศเท่านั้น กรุณาถามแนวโน้มแยกจากจังหวัดและตัวชี้วัดอื่น')
    if plan.group_by == 'period' and not names and any(getattr(plan,k) is not None for k in ['min_population','min_credits','min_gpp','max_branch_density']):
        raise Clarification('เกณฑ์คัดจังหวัดใช้กับการจัดอันดับรายจังหวัด ไม่ใช้กรองยอดรวมประเทศโดยอัตโนมัติ')
    params = {'limit': plan.limit, 'end': end}
    raw_filters = []
    for i,name in enumerate(names):
        matches = [p for p in _provinces() if name.lower() in {str(p['name_th']).lower(),str(p['name_en']).lower()}]
        if len(matches) != 1:
            raise Clarification(f'ไม่พบจังหวัดที่ตรงกับ {name!r}')
        params[f'province_{i}'] = matches[0]['province_code']
    if names:
        raw_filters.append('province_code IN ('+','.join(':province_'+str(i) for i in range(len(names)))+')')
    if plan.exclude_bangkok:
        raw_filters.append('province_code <> 10')
    provincial = plan.group_by == 'province' or bool(names)
    dimensions = 'province_code,name_th,name_en,period' if provincial else 'period'
    aggregates = ','.join(expr+' AS '+key for key,(expr,_,_) in BASE.items())
    aggregates += ',SUM(population) AS population,MAX(population_reference_year) AS population_reference_year,MAX(gpp_reference_year) AS gpp_reference_year'
    measures = f"SELECT {dimensions},{aggregates} FROM mart_province_month WHERE {' AND '.join(raw_filters) or 'TRUE'} GROUP BY {dimensions}"
    yoy = ','.join(f'100.0*(n.{base}-p.{base})/NULLIF(p.{base},0) AS {key}' for key,base in YOY.items())
    join = "p.period=(n.period-interval '1 year')::date"+(' AND p.province_code=n.province_code' if provincial else '')
    filters = ['period = :end' if plan.group_by == 'province' else 'period <= :end']
    if plan.start_period and plan.group_by == 'period':
        filters.append('period >= :start')
        params['start'] = plan.start_period
    for field,column,sign in [('min_population','population','>='),('min_credits','credits','>='),('min_gpp','gpp','>='),('max_branch_density','branches_per_100k','<=')]:
        value = getattr(plan,field)
        if value is not None:
            if field in plan.strict_filters:
                sign = '>'
            filters.append(f'{column} {sign} :{field}')
            params[field] = value
    ctes = f"WITH measures AS ({measures}), compared AS (SELECT n.*,{yoy} FROM measures n LEFT JOIN measures p ON {join}), scoped AS (SELECT * FROM compared WHERE {' AND '.join(filters)})"
    columns = ('province_code,name_th,name_en,' if provincial else '')+'period,'+','.join(keys)+f',{plan.metric} AS value,population_reference_year,gpp_reference_year'
    direction = 'ASC' if plan.ascending else 'DESC'
    if plan.group_by == 'province':
        sql = ctes+f", eligible AS (SELECT * FROM scoped WHERE {plan.metric} IS NOT NULL) SELECT {columns},RANK() OVER (ORDER BY {plan.metric} {direction}) AS rank,COUNT(*) OVER () AS eligible_count FROM eligible ORDER BY {plan.metric} {direction},province_code LIMIT :limit"
    else:
        sql = ctes+f", recent_periods AS (SELECT DISTINCT period FROM scoped ORDER BY period DESC LIMIT :limit) SELECT {columns} FROM scoped WHERE period IN (SELECT period FROM recent_periods) ORDER BY period"+(',province_code' if provincial else '')
    _validate_query(sql)
    return sql,params

def _validate_query(query: str):
    parsed = sqlglot.parse(query,read='postgres')
    if len(parsed) != 1 or parsed[0] is None or parsed[0].key != 'select':
        raise ValueError('Only one SELECT is allowed')
    tree = parsed[0]
    if any(n.key in {'insert','update','delete','drop','create','command','into'} for n in tree.walk()):
        raise ValueError('Read-only SELECT required')
    ctes = {c.alias_or_name for c in tree.find_all(sqlglot.exp.CTE)}
    if {t.name for t in tree.find_all(sqlglot.exp.Table)}-ctes != {'mart_province_month'}:
        raise ValueError('Only the safe mart is queryable')

def execute_plan(plan: QueryPlan) -> dict:
    sql,params = compile_query(plan)
    with read_engine().connect() as conn:
        with conn.begin():
            conn.execute(text('SET TRANSACTION READ ONLY'))
            conn.execute(text("SET LOCAL statement_timeout = '10s'"))
            rows = [dict(r) for r in conn.execute(text(sql),params).mappings()]
    for row in rows:
        for k,v in row.items():
            if isinstance(v,date):
                row[k] = v.isoformat()
            elif isinstance(v,Decimal):
                row[k] = float(v)
    keys = requested_metrics(plan)
    sources = ['BOT FI_CB_011_S5']
    if any('person' in k or k == 'branches_per_100k' for k in keys) or plan.min_population is not None or plan.max_branch_density is not None:
        sources.append('DOPA registered population')
    if 'gpp' in keys or plan.min_gpp is not None:
        sources.append('NESDC GPP 2024p')
    if plan.metric == 'policy_rate':
        sources = ['BOT MPC policy decision workbook']
    chart = plan.chart if plan.chart != 'auto' else ('line' if plan.group_by == 'period' else 'bar')
    notice = ''
    if chart == 'line' and plan.group_by != 'period':
        chart,notice = 'bar','ไม่มีแกนเวลา จึงใช้กราฟแท่งแทนกราฟเส้น'
    scope = 'เฉพาะจังหวัดที่เลือก' if plan.province or plan.provinces else ('ไม่รวมกรุงเทพมหานคร' if plan.exclude_bangkok else 'ทุกจังหวัด')
    return {'plan':plan.model_dump(mode='json'),'metric_label':METRICS[plan.metric][1],'unit':METRICS[plan.metric][2],
      'metrics':[{'key':k,'label':METRICS[k][1],'unit':METRICS[k][2],'formula':BASE[k][0] if k in BASE else '(current / same month previous year - 1) * 100'} for k in keys],
      'chart':{'kind':chart,'notice':notice},'scope':scope,'period':str(params['end']),
      'eligible_count':int(rows[0].get('eligible_count',0)) if rows else 0,
      'sql':sql,'parameters':{k:str(v) for k,v in params.items()},'rows':rows,'sources':sources,
      'caveat':('อัตราดอกเบี้ยนโยบายเป็นบริบทระดับประเทศ ณ สิ้นเดือน ไม่พิสูจน์ผลเชิงสาเหตุ' if plan.metric == 'policy_rate' else
        'ยอดคงค้างไม่ใช่ยอดปล่อยใหม่; กรุงเทพฯ อาจรวมการบันทึกสำนักงานใหญ่; ประชากรเป็นจำนวนตามทะเบียนบ้าน อัตราต่อคนไม่ใช่หนี้เฉลี่ยรายบุคคล และต่อสาขาไม่ใช่ผลงานของสาขา; ปีอ้างอิงต่างจากงวดธนาคาร; หากไม่มีฐานเปรียบเทียบปีก่อน จะไม่แสดงค่า YoY แทนการแสดงเป็นศูนย์')}
