"""Explicit Thai intent parsing and semantic checks shared by every provider."""
from __future__ import annotations
import re
from datetime import date
from .query import Clarification, QueryPlan, METRICS, _provinces

PATTERNS = [
 ('credits_per_person',r'(?:สินเชื่อ|เครดิต|loans?|credits?)\s*(?:เฉลี่ย\s*)?(?:เทียบกับ|เทียบ|ต่อ|หารด้วย|per)\s*(?:ประชากร(?:ทะเบียน)?|คน|หัว|person|capita)'),
 ('credits_per_branch',r'(?:สินเชื่อ|เครดิต|loans?|credits?)\s*(?:เทียบกับ|เทียบ|ต่อ|หารด้วย|per)\s*(?:จำนวน)?(?:สาขา|branch(?:es)?)'),
 ('credit_deposit_ratio',r'(?:สินเชื่อ|เครดิต|loan)\s*(?:เทียบกับ|ต่อ|to)\s*(?:เงินฝาก|deposit)(?: ratio)?|\bldr\b'),
 ('branches_per_100k',r'สาขา\s*(?:เทียบกับ|ต่อ)\s*(?:ประชากร|แสน|100,?000)|branch density|branches per (?:person|capita|100,?000)'),
 ('deposits_per_person',r'(?:เงินฝาก|deposit)\s*(?:เทียบกับ|ต่อ|per)\s*(?:ประชากร(?:ทะเบียน)?|หัว|คน|person|capita)'),
 ('policy_rate',r'ดอกเบี้ยนโยบาย|policy rate'),
 ('gpp',r'\bgpp\b|ผลิตภัณฑ์จังหวัด'),
 ('credits',r'สินเชื่อ|เครดิต|\bcredits?\b|\bloans?\b'),
 ('deposits',r'เงินฝาก|\bdeposits?\b'),
 ('branches',r'สาขา|\bbranches\b'),
]
MONTHS = ['มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม']
SHORT = ['ม.ค.','ก.พ.','มี.ค.','เม.ย.','พ.ค.','มิ.ย.','ก.ค.','ส.ค.','ก.ย.','ต.ค.','พ.ย.','ธ.ค.']

def normalize(question):
    return re.sub(r'\s+',' ',question.strip().lower().replace('เเ','แ'))

def safety_check(question):
    q = normalize(question)
    if any(word in q for word in ['รายอำเภอ','รายตำบล','รายวัน','รายสัปดาห์','เดือนหน้า','ปีหน้า']):
        raise Clarification('ข้อมูลรองรับระดับจังหวัดและงวดรายเดือนที่มีในคลัง ไม่รองรับขอบเขตหรือช่วงอนาคตที่ถาม', unsupported=True)
    if any(word in q for word in ['เดือนที่แล้ว','เดือนก่อน','ปีที่แล้ว'] ) and not any(word in q for word in ['yoy','เทียบ','ปีก่อน']):
        raise Clarification('กรุณาระบุเดือนและปีที่ต้องการ เพื่อไม่สับสนระหว่างวันที่ปัจจุบันกับงวดล่าสุดในคลัง', reason='ambiguous_period')
    if re.search(r'(?:ประชากร|สินเชื่อ|เงินกู้|เครดิต|gpp)\s*(?:น้อยกว่า|ต่ำกว่า|ไม่เกิน|<|≤|=(?!=))',q):
        raise Clarification('ยังไม่รองรับตัวกรองค่าสูงสุดนี้ ระบบจะไม่ละเงื่อนไขแล้วตอบยอดอื่นแทน', unsupported=True)
    if re.search(r'(?:เงินฝาก|สาขา)\s*(?:มากกว่า|เกิน|อย่างน้อย|>=|>|≥)\s*\d',q):
        raise Clarification('ยังไม่รองรับตัวกรองขั้นต่ำของเงินฝากหรือจำนวนสาขา กรุณาเลือกตัวกรองที่ระบบรองรับ', unsupported=True)
    if any(word in q for word in ['npl','หนี้เสีย','เลขบัญชี','ข้อมูลลูกค้า','รายชื่อลูกค้า','รายธนาคาร','ธนาคาร a','ธนาคารกสิกร','ธนาคารกรุงไทย','ธนาคารไทยพาณิชย์','ธนาคารกรุงเทพ','กำไร','รายได้สาขา','อนุมัติสินเชื่อ','พยากรณ์','คาดการณ์','ทำนาย','ราคาหุ้น','อากาศ','delete ','drop ','api key','รหัสผ่าน','ignore previous']):
        raise Clarification('ไม่มีข้อมูลหรือไม่รองรับคำถามนี้: ใช้ได้เฉพาะข้อมูลสาธารณะระดับจังหวัดและบริบทดอกเบี้ย ไม่ตอบข้อมูลลูกค้า รายธนาคาร NPL การพยากรณ์หรือคำสั่งแก้ฐานข้อมูล',unsupported=True)
    if re.search(r'(สินเชื่อ|เงินฝาก)\s*(ต่อ|เทียบกับ|หารด้วย)\s*(gpp|รายได้|พื้นที่|ลูกค้า)',q):
        raise Clarification('ยังไม่มีนิยามตัวชี้วัดอัตราส่วนนี้ จึงไม่แทนด้วยยอดรวม กรุณาเลือกตัวชี้วัดที่รองรับ',unsupported=True)
    if ('ประชากร' in q and 'สาขา' in q and 'สินเชื่อ' in q and
        not ('สินเชื่อต่อประชากร' in q and 'สินเชื่อต่อสาขา' in q)):
        raise Clarification('ต้องการจัดอันดับสินเชื่อต่อประชากร สินเชื่อต่อสาขา หรือดูทั้งสองโดยจัดอันดับด้วยตัวไหน?',
            ['สินเชื่อต่อประชากรมากที่สุด','สินเชื่อต่อสาขามากที่สุด','สินเชื่อต่อประชากรสูงสุด พร้อมสินเชื่อต่อสาขา'])

def extract_metrics(q):
    remaining, found = q, []
    for metric, pattern in PATTERNS:
        matches = list(re.finditer(pattern,remaining))
        if matches:
            found.append((matches[0].start(),metric))
            remaining = re.sub(pattern,lambda m: ' '*len(m.group()),remaining)
    return [metric for _,metric in sorted(found)]


def explicit_dates(q):
    dates = []
    for value in re.findall(r'\b\d{4}-\d{2}(?:-\d{2})?\b', q):
        year, month = map(int, value[:7].split('-'))
        dates.append(date(year-543 if year > 2400 else year, month, 1))
    for i, (full, short) in enumerate(zip(MONTHS, SHORT), 1):
        for match in re.finditer(r'(?:'+re.escape(full)+'|'+re.escape(short)+r')\s*(\d{4})', q):
            year = int(match.group(1))
            dates.append(date(year-543 if year > 2400 else year, i, 1))
    return sorted(set(dates))

def parse_question(question: str, context: dict | None = None, version: str = 'v1', *, province_catalog=None) -> QueryPlan:
    if version in ['v2','v3','v4']:
        # Development-driven lexical normalization; preserve denominator guards.
        question = re.sub(r'ยอดออม|เงินออม','เงินฝาก',question)
        question = re.sub(r'เงินกู้','สินเชื่อ',question)
        question = question.replace('ตามเดือน','รายเดือน')
    safety_check(question)
    q = normalize(question)
    if not q:
        raise Clarification('กรุณาพิมพ์คำถาม')
    metric_text = re.sub(r'(?:gpp|สินเชื่อ|ประชากร)\s*(?:เกิน|มากกว่า|อย่างน้อย|>=|>|≥)\s*[\d,.]+\s*(?:ล้านล้านบาท|พันล้านบาท|ล้านบาท|แสนบาท|พันบาท|ล้านคน|แสนคน|พันคน|ล้าน|พัน|แสน|บาท|คน)?','',q)
    keys = extract_metrics(metric_text)
    ratio_remainder = q
    for _,pattern in PATTERNS[:5]:
        ratio_remainder = re.sub(pattern,'',ratio_remainder)
    if re.search(r'(สินเชื่อ|เงินฝาก|สาขา)\s*(?:เทียบกับ|ต่อ|หารด้วย)',ratio_remainder):
        raise Clarification('ยังไม่ชัดเจนว่าหารด้วยอะไร จึงไม่ตอบเป็นยอดรวม กรุณาระบุตัวหารที่รองรับ',unsupported=True)
    previous = QueryPlan.model_validate(context) if context else None
    followup = not keys and previous is not None and any(w in q for w in ['ไม่เอา','ไม่รวม','รวมกรุงเทพ','เอา ','อันดับ','ปีก่อน','กราฟ','ตาราง','ย้อนหลัง','แทน','ปี ','งวด','เดือน','ประชากรเกิน','ประชากรอย่างน้อย'])
    if not keys and not followup:
        raise Clarification('กรุณาระบุตัวชี้วัด เช่น สินเชื่อต่อประชากร สินเชื่อต่อสาขา เงินฝาก หรือสาขา')
    data = previous.model_dump() if followup else {'metric': keys[0], 'metrics': keys, 'group_by':'province'}
    # A metric-changing continuation can retain the confirmed scope, not arbitrary old intent.
    if keys and previous and any(w in q for w in ['แทน','เปลี่ยนเป็น','แล้วถ้า']):
        data = {**previous.model_dump(),'metric':keys[0],'metrics':keys}
    if keys:
        data.update(metric=keys[0],metrics=keys)
    ordered = re.search(r'(?:เรียงตาม|จัดอันดับ(?:ด้วย|ตาม))\s*(.+)',q)
    if ordered:
        sort_keys = extract_metrics(ordered.group(1))
        if not sort_keys:
            raise Clarification('กรุณาระบุว่าจัดอันดับด้วยตัวชี้วัดใด')
        data['metric'] = sort_keys[0]
    ranking = any(w in q for w in ['สูงสุด','ต่ำสุด','มากที่สุด','น้อยที่สุด','อันดับ','top','bottom'])
    if len(keys)>1 and ranking and not ordered and not any(w in q for w in ['พร้อม','ประกอบ','แสดงเพิ่ม']):
        raise Clarification('มีหลายตัวชี้วัด ต้องการจัดอันดับด้วยตัวไหน?', [f'{METRICS[k][1]}สูงสุด พร้อม '+ ' และ '.join(METRICS[other][1] for other in keys if other!=k) for k in keys])
    aliases = {'กรุงเทพ':'กรุงเทพมหานคร','กทม.':'กรุงเทพมหานคร','กทม':'กรุงเทพมหานคร'}
    named = []
    excluded = any(w in q for w in ['ไม่รวมกรุงเทพ','ไม่เอากรุงเทพ','ไม่รวม กทม','ไม่เอา กทม','exclude bangkok'])
    for p in (_provinces() if province_catalog is None else province_catalog):
        names = [str(p['name_th']),str(p['name_en']).lower()]
        if p['province_code']==10:
            names += list(aliases)
        if any(n and n.lower() in q for n in names) and not (p['province_code']==10 and excluded):
            named.append(p['name_th'])
    if len(named)>4:
        raise Clarification('เปรียบเทียบได้สูงสุด 4 จังหวัด')
    if named:
        data.update(province=named[0] if len(named)==1 else None,provinces=named if len(named)>1 else [],intent='lookup' if len(named)==1 else 'comparison')
    if excluded:
        data['exclude_bangkok']=True
        if data.get('province')=='กรุงเทพมหานคร':
            data['province']=None
        data['provinces']=[n for n in data.get('provinces',[]) if n!='กรุงเทพมหานคร']
    if 'รวมกรุงเทพ' in q and not excluded:
        data['exclude_bangkok']=False
    trend = any(w in q for w in ['แนวโน้ม','ย้อนหลัง','รายเดือน','trend']) or data['metric']=='policy_rate'
    if trend:
        data.update(group_by='period',intent='trend',limit=25)
    elif ranking:
        data.update(group_by='province',intent='comparison' if len(named)>1 else 'lookup' if named else 'ranking')
    match = re.search(r'(?:top|อันดับ|สูงสุด|ต่ำสุด|เอา|ย้อนหลัง'+ ('|มากที่สุด|น้อยที่สุด' if version in ['v2','v3','v4'] else '') +r')\s*(\d{1,2})(?!\d)',q)
    if match:
        data['limit']=max(1,min(int(match.group(1)),77))
    if version == 'v4' and not match:
        count = re.search(r'(?:ขอ|แสดง)\s*(\d{1,2})(?!\d)\s*จังหวัด', q)
        if count:
            data['limit'] = max(1, min(int(count.group(1)), 77))
    data['ascending']=any(w in q for w in ['ต่ำสุด','น้อยสุด','น้อยที่สุด','bottom']) if ranking else data.get('ascending',False)
    yoy = any(w in q for w in ['yoy','ปีก่อน','เทียบปี','เติบโต','โตเร็ว'])
    if yoy:
        data['include_yoy']=True
        if ranking and keys and not any(w in q for w in ['พร้อม','ประกอบ','แสดงเพิ่ม']) and data['metric'] in ['credits','deposits','branches','credits_per_person','credits_per_branch']:
            data['metric'] += '_yoy_pct'
            data['metrics']=[data['metric'],*keys]
    dates = explicit_dates(q)
    if dates:
        dates=sorted(dates)
        data['end_period']=dates[-1]
        if len(dates)>1:
            data.update(start_period=dates[0],group_by='period',intent='trend')
    elif re.search(r'(?:ปี|งวด)\s*(?:25|20)\d{2}',q):
        raise Clarification('กรุณาระบุเดือนด้วย ข้อมูลสินเชื่อเป็นยอดคงค้างรายเดือน ไม่รวมยอดทั้งปี', reason='ambiguous_period')
    filter_patterns = [
      ('min_population',r'ประชากร\s*(?:เกิน|มากกว่า|อย่างน้อย|>=|>|≥)\s*([\d,]+(?:\.\d+)?)\s*(พัน|แสน|ล้าน)?'),
      ('min_credits',r'สินเชื่อ\s*(?:เกิน|มากกว่า|อย่างน้อย|>=|>|≥)\s*([\d,]+(?:\.\d+)?)'),
      ('min_gpp',r'gpp\s*(?:เกิน|มากกว่า|อย่างน้อย|>=|>|≥)\s*([\d,]+(?:\.\d+)?)'),
      ('max_branch_density',r'สาขาต่อ(?:ประชากร)?แสน\s*(?:ไม่เกิน|<=|≤)\s*([\d,]+(?:\.\d+)?)'),
    ]
    for field,pattern in filter_patterns:
        m=re.search(pattern,q)
        if m:
            data[field]=float(m.group(1).replace(',',''))*({'พัน':1000,'แสน':100000,'ล้าน':1000000}.get(m.group(2),1) if field=='min_population' else 1)
            if field.startswith('min_') and re.search(r'(?:เกิน|มากกว่า|>(?!=))',m.group()):
                data['strict_filters']=list(dict.fromkeys([*data.get('strict_filters',[]),field]))
            elif field in data.get('strict_filters',[]):
                data['strict_filters'].remove(field)
            if field in ['min_credits','min_gpp']:
                suffix=q[m.end():].lstrip()
                if suffix.startswith('บาท'):
                    data[field]/=1000000
                elif suffix.startswith('พันล้าน'):
                    data[field]*=1000
                elif suffix.startswith('ล้านล้าน'):
                    data[field]*=1000000
                elif suffix.startswith('พันบาท'):
                    data[field]/=1000
                elif suffix.startswith('แสนบาท'):
                    data[field]/=10
    if 'ตาราง' in q:
        data['chart']='table'
    elif 'กราฟแท่ง' in q:
        data['chart']='bar'
    elif 'กราฟเส้น' in q:
        data['chart']='line'
    elif 'กราฟ' in q:
        data['chart']='auto'
    return QueryPlan.model_validate(data)
