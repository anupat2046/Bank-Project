"""Evidence checks against explicit user constraints, never benchmark answers.

Conservative lexical coverage is not a proof of understanding arbitrary language.
Reject conflicts rather than silently replacing the model's plan.
"""
import re
from .intent import normalize, extract_metrics, explicit_dates, safety_check
from .query import Clarification, rules_plan, requested_metrics


def validate_semantics(question, plan, context=None):
    safety_check(question)
    q = normalize(question)
    dates = explicit_dates(q)
    if dates and plan.end_period != dates[-1]:
        raise Clarification('ช่วงเวลาในแผนไม่ตรงกับคำถาม กรุณายืนยันเดือนและปีอีกครั้ง', reason='semantic_conflict')
    if len(dates) > 1 and (plan.start_period != dates[0] or plan.group_by != 'period'):
        raise Clarification('คำถามระบุช่วงเวลา แต่แผนไม่ได้เปรียบเทียบตามช่วงนั้น', reason='semantic_conflict')
    if not dates and re.search(r'(?:ปี|งวด)\s*(?:25|20)\d{2}', q):
        raise Clarification('กรุณาระบุเดือนด้วย ยอดคงค้างไม่สามารถรวมทั้งปีได้', reason='ambiguous_period')
    try:
        reference = rules_plan(question, context, 'v4')
    except Clarification as exc:
        if exc.unsupported or exc.choices or exc.reason != 'unrecognized_language':
            raise
        reference = None
    # Recognized ratios must remain present even when another phrase needs the LLM.
    keys = extract_metrics(q)
    ratios = {k for k in keys if k.endswith(('_per_person', '_per_branch')) or k in ['credit_deposit_ratio','branches_per_100k']}
    actual = set(requested_metrics(plan))
    if any(k not in actual and k+'_yoy_pct' not in actual for k in ratios):
        raise Clarification('ตัวหารในแผนไม่ตรงกับคำถาม กรุณายืนยันตัวชี้วัด', reason='semantic_conflict')
    if reference:
        fields = ['metric','metrics','province','provinces','exclude_bangkok','group_by',
                  'ascending','include_yoy','min_population','min_credits','min_gpp',
                  'max_branch_density','strict_filters']
        # Latest means unresolved latest for standalone requests, not the current date.
        if not context or not any(w in q for w in ['แทน','เปลี่ยนเป็น','แล้วถ้า']):
            fields += ['end_period','start_period']
        if re.search(r'(?:top|อันดับ|สูงสุด|ต่ำสุด|เอา|ย้อนหลัง|มากที่สุด|น้อยที่สุด|ขอ|แสดง)\s*\d', q):
            fields.append('limit')
        for field in fields:
            expected, actual_value = getattr(reference, field), getattr(plan, field)
            if field == 'metrics':
                mismatch = not set(requested_metrics(reference)).issubset(requested_metrics(plan))
            elif field in ['provinces','strict_filters']:
                mismatch = set(expected) != set(actual_value)
            else:
                mismatch = expected != actual_value
            if mismatch:
                raise Clarification('แผนวิเคราะห์ขัดกับตัวชี้วัด จังหวัด เวลา หรือเงื่อนไขที่ระบุ กรุณายืนยันคำถามอีกครั้ง', reason='semantic_conflict')
    return plan
