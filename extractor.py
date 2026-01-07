import re
import json
from dataclasses import dataclass, asdict
from typing import Optional, Tuple
from datetime import datetime

RAW_TEXT_MAX_LEN = 200

@dataclass
class ConversationData:
    timestamp: Optional[str] = None
    sentiment: Optional[str] = None
    member_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    address_status: Optional[str] = None
    member_status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    health_plan: Optional[str] = None
    contract_type: Optional[str] = None
    codes: Optional[str] = None
    change_request: Optional[str] = None
    raw_text: Optional[str] = None

MONTHS_RE = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
STATE_RE = r"[A-Za-z]{2}"
EXCEL_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def now_ts() -> str:
    return datetime.now().strftime(EXCEL_DATE_FORMAT)

POS_WORDS = ["thank", "thanks", "good", "resolved", "correct", "ok", "okay", "completed"]
NEG_WORDS = ["error", "issue", "problem", "wrong", "termed", "terminate", "typo", "fix", "incorrect", "should be inactive", "should be", "eff"]

def analyze_sentiment(text: str) -> str:
    if not text:
        return "Neutral"
    t = text.lower()
    score = 0
    for w in POS_WORDS:
        if w in t:
            score += 1
    for w in NEG_WORDS:
        if w in t:
            score -= 1
    if score > 0:
        return "Positive"
    if score < 0:
        return "Negative"
    return "Neutral"

def normalize_plan(plan_raw: Optional[str]) -> Optional[str]:
    if not plan_raw:
        return None
    p = plan_raw.strip().lower()
    if "hmo" in p:
        return "HMO"
    if "ppo" in p:
        return "PPO"
    if "epo" in p:
        return "EPO"
    if "medicare" in p or "medadv" in p or "med adv" in p:
        return "Medicare Adv"
    if "commercial" in p or "comm" in p:
        return "Commercial"
    return plan_raw.strip()

def normalize_status(status_raw: Optional[str]) -> Optional[str]:
    if not status_raw:
        return None
    s = status_raw.strip().lower()
    if any(token in s for token in ["active", "actv", "active from", "active starting", "active frm"]):
        return "ACTIVE"
    if any(token in s for token in ["inactive", "inactivate", "should be inactive"]):
        return "INACTIVE"
    if any(token in s for token in ["term", "termed", "terminated", "term eff", "termed effective"]):
        return "TERMINATED"
    return status_raw.strip()

def extract_date_like(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{1,2}\.\d{1,2}\.\d{2,4})\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(" + MONTHS_RE + r")[\s\-\.]*\d{1,2},?\s*\d{4}\b", text, flags=re.I)
    if m:
        mm = re.search(r"\b(?:" + MONTHS_RE + r")[\s\-\.]*\d{1,2},?\s*\d{4}\b", text, flags=re.I)
        return mm.group(0)
    return None

def extract_member_id(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(?:member(?:\s*id)?|memb|memberid|Member\s*ID)[:\s#\-]*([0-9]{4,12})", text, flags=re.I)
    if m:
        return m.group(1)
    m = re.search(r"\bmember[\s\-:]*([0-9]{6,12})\b", text, flags=re.I)
    if m:
        return m.group(1)
    return None

def extract_names(text: str) -> Tuple[Optional[str], Optional[str]]:
    if not text:
        return None, None
    m = re.search(r"(?:Name|name)[:\s\-]*([A-Z][A-Za-z\'\.\-]+(?:\s+[A-Z][A-Za-z\'\.\-]+){0,3})", text)
    if m:
        parts = m.group(1).strip().split()
        if len(parts) == 1:
            return parts[0], None
        return parts[0], " ".join(parts[1:])
    lines = [ln.strip() for ln in re.split(r"[\r\n]+", text) if ln.strip()]
    for ln in lines:
        tokens = ln.split()
        if 2 <= len(tokens) <= 4 and all(re.match(r"^[A-Z][A-Za-z\'\.\-]+$", t) for t in tokens):
            return tokens[0], " ".join(tokens[1:])
    m = re.search(r"\b([A-Z][a-zA-Z'\-]+),\s*([A-Z][A-Za-z'\-]+(?:\s+[A-Z])?)", text)
    if m:
        return m.group(2), m.group(1)
    return None, None

def extract_address_city_state_zip(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    if not text:
        return None, None, None, None
    m = re.search(r"(\d{1,6}\s+[^\n,]+?)\s+([A-Za-z][A-Za-z\s\.']{1,40})[,]?\s+(" + STATE_RE + r")\.?\s*(\d{5})", text, flags=re.I)
    if m:
        addr = m.group(1).strip()
        city = m.group(2).strip()
        state = m.group(3).upper().strip()
        zipcode = m.group(4).strip()
        return addr, city, state, zipcode
    m = re.search(r"(\d{1,6}\s+[^\n,]+?)\s+([A-Za-z][A-Za-z\s\.']{1,40})\s+(" + STATE_RE + r")\s*(\d{5})", text, flags=re.I)
    if m:
        return m.group(1).strip(), m.group(2).strip(), m.group(3).upper().strip(), m.group(4).strip()
    if re.search(r"\b(address\s+stays\s+same|address\s+same on file|address\s+same|same on file|address\s+unchanged)\b", text, flags=re.I):
        return None, None, None, None
    m = re.search(r"([A-Za-z][A-Za-z\s\.']{1,40})\s+(" + STATE_RE + r")\s+(\d{5})", text, flags=re.I)
    if m:
        return None, m.group(1).strip(), m.group(2).upper().strip(), m.group(3).strip()
    return None, None, None, None

def extract_member_status(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(status|status\s*should\s*be|status:)?\s*(active|inactive|term(?:ed|)\b|terminated|termed|term|should be inactive|should be active|active from|active starting|active frm)[\w\s]*", text, flags=re.I)
    if m:
        snippet = m.group(0)
        if re.search(r"\b(term(?:ed|)|termed|terminated|term eff|termed effective|terminate)\b", snippet, flags=re.I) or re.search(r"\bterm(?:ed)?\b", text, flags=re.I):
            return "TERMINATED"
        if re.search(r"\binactive\b", snippet, flags=re.I):
            return "INACTIVE"
        if re.search(r"\bactive\b", snippet, flags=re.I):
            return "ACTIVE"
    m2 = re.search(r"(should be (active|inactive))", text, flags=re.I)
    if m2:
        return m2.group(2).upper()
    return None

def extract_plan(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(plan(?:\s*type)?|health plan|pln|new plan|Plan)\s*[:=\-]*\s*([A-Za-z0-9\-\s]+)", text, flags=re.I)
    if m:
        raw = m.group(2).strip()
        raw = re.split(r"[,;]|status|contract|begin|cover|coverage|codes|code", raw, flags=re.I)[0].strip()
        return normalize_plan(raw)
    if re.search(r"\bHMO\b", text, flags=re.I):
        return "HMO"
    if re.search(r"\bPPO\b", text, flags=re.I):
        return "PPO"
    if re.search(r"\bEPO\b", text, flags=re.I):
        return "EPO"
    if re.search(r"\bMedicare\s*Adv\b", text, flags=re.I) or re.search(r"\bMedicare\b", text, flags=re.I):
        return "Medicare Adv"
    if re.search(r"\bCommercial\b|\bcomm\b", text, flags=re.I):
        return "Commercial"
    return None

def extract_contract(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(?:Contract|Contract\s*type|contract|contract:)\s*[:=\-]*\s*([0-9A-Za-z\-]{1,10})", text, flags=re.I)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"\bcontract\s+(\d)\b", text, flags=re.I)
    if m2:
        return m2.group(1)
    return None

def extract_codes(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(?:codes?|cd|code|health code)[:\s]*([0-9]{3,6}(?:\s*[,/;\s]\s*[0-9]{3,6})*)", text, flags=re.I)
    if m:
        raw = m.group(1)
        codes = re.split(r"[,/;]\s*|\s{2,}|\s+", raw.strip())
        codes = [c.strip() for c in codes if re.match(r"^\d{3,6}$", c.strip())]
        if codes:
            seen = []
            out = []
            for c in codes:
                if c not in seen:
                    seen.append(c)
                    out.append(c)
            return ", ".join(out)
    return None

def extract_change_request(text: str) -> Optional[str]:
    if not text:
        return None
    patterns = [
        r"(?:change request[:\-\s]*)(.+)$",
        r"(?:please update[:\-\s]*)(.+)$",
        r"(?:please revise[:\-\s]*)(.+)$",
        r"(?:request to update[:\-\s]*)(.+)$",
        r"(?:need to change[:\-\s]*)(.+)$",
        r"(?:please process[:\-\s]*)(.+)$",
        r"(?:request[:\-\s]*)(.+)$",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.I | re.S)
        if m:
            return m.group(1).strip()[:RAW_TEXT_MAX_LEN]
    m2 = re.search(r"^(Please update.+|Request to update.+|Need eligibility.+|Please revise.+)", text, flags=re.I | re.M)
    if m2:
        return m2.group(1).strip()[:RAW_TEXT_MAX_LEN]
    if re.search(r"\bplease update|request to update|need eligibility|update elig|terminate member|terminate|terminate|please revise|eligibility chg", text, flags=re.I):
        return text.strip()[:RAW_TEXT_MAX_LEN]
    return None

def try_parse_json(text: str) -> Optional[ConversationData]:
    if not text or not text.strip():
        return None
    text_stripped = text.strip()
    if not text_stripped.startswith("{"):
        return None
    try:
        obj = json.loads(text_stripped)
        if not isinstance(obj, dict):
            return None
        d = ConversationData()
        d.timestamp = now_ts()
        d.sentiment = analyze_sentiment(text_stripped[:RAW_TEXT_MAX_LEN])
        d.raw_text = text_stripped[:RAW_TEXT_MAX_LEN]
        mapping = {
            "member_id": "member_id",
            "first_name": "first_name",
            "last_name": "last_name",
            "dob": "dob",
            "address": "address",
            "city": "city",
            "state": "state",
            "zip": "zip_code",
            "zip_code": "zip_code",
            "address_status": "address_status",
            "status": "member_status",
            "member_status": "member_status",
            "start_date": "start_date",
            "end_date": "end_date",
            "plan": "health_plan",
            "health_plan": "health_plan",
            "contract_type": "contract_type",
            "codes": "codes",
            "change_request": "change_request",
        }
        for k, v in obj.items():
            if k in mapping:
                setattr(d, mapping[k], v)
        if d.address_status is None:
            if d.address is None:
                d.address_status = "missing"
        if d.member_id is not None:
            d.member_id = str(d.member_id)
        return d
    except Exception:
        return None

def extract_attributes(text: str) -> ConversationData:
    json_data = try_parse_json(text)
    if json_data:
        if json_data.change_request is None:
            json_data.change_request = extract_change_request(text)
        return json_data

    data = ConversationData()
    if not text or not text.strip():
        return data

    data.raw_text = text.strip()[:RAW_TEXT_MAX_LEN]
    data.timestamp = now_ts()
    data.sentiment = analyze_sentiment(text)

    joined_lines = "\n".join([ln.strip() for ln in text.splitlines() if ln.strip()])
    compact = " ".join(joined_lines.split())

    data.member_id = extract_member_id(compact)
    fn, ln = extract_names(text)
    data.first_name = fn
    data.last_name = ln

    m = re.search(r"(?:DOB|Date of Birth|dob|DOB:)\s*[:\-]*\s*([^\n,;]+(?:[,\s]\s*\d{4})?)", text, flags=re.I)
    if m:
        maybe = m.group(1)
        dd = extract_date_like(maybe) or maybe.strip()
        data.dob = dd
    else:
        dd = extract_date_like(text)
        if dd:
            data.dob = dd

    if re.search(r"\b(address\s+stays\s+same|address\s+same on file|address\s+same|same on file|address\s+unchanged|Address same on file)\b", text, flags=re.I):
        data.address_status = "unchanged"
        data.address = None
        data.city = None
        data.state = None
        data.zip_code = None
    else:
        addr, city, st, zp = extract_address_city_state_zip(text)
        data.address = addr
        data.city = city
        data.state = st
        data.zip_code = zp
        if addr:
            data.address_status = "updated"
        else:
            if data.address_status is None:
                data.address_status = "missing"

    raw_status = extract_member_status(text)
    data.member_status = normalize_status(raw_status) if raw_status else None

    m = re.search(r"(?:coverage\s*start|coverage\s*begins|coverage\s*begin\s*date|coverage\s*begin|coverage\s*from|cover\s*date|cover\s*date|begin(?: date)?|Begin)\s*[:\-\s]*([^\n,;]+)", text, flags=re.I)
    if m:
        dd = extract_date_like(m.group(1)) or m.group(1).strip()
        data.start_date = dd
    else:
        m2 = re.search(r"\b(begin|begin date|beginning)\b[:\-\s]*([^\s,;]+)", text, flags=re.I)
        if m2:
            data.start_date = extract_date_like(m2.group(2)) or m2.group(2).strip()
        else:
            m3 = re.search(r"\b(?:active(?:\s*from|\s*starting|\s*frm)?|active\s+starting|active\s+from)\s*([0-9]{1,2}[\/\.-][0-9]{1,2}[\/\.-][0-9]{2,4}|\b" + MONTHS_RE + r"\s*\d{1,2},?\s*\d{4})", text, flags=re.I)
            if m3:
                data.start_date = m3.group(1)

    m = re.search(r"(?:Plan\s*End\s*Date|Plan\s*End|plan end date|plan end)\s*[:\-\s]*([^\n,;]+)", text, flags=re.I)
    if m:
        data.end_date = extract_date_like(m.group(1)) or m.group(1).strip()
    else:
        m2 = re.search(r"(?:term(?:ed|)|terminated|termed|terminate|termed effective|term eff|term effective)\s*(?:effective|eff|:)?\s*([0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4}|\b" + MONTHS_RE + r"\s*\d{1,2},?\s*\d{4})", text, flags=re.I)
        if m2:
            data.end_date = extract_date_like(m2.group(1)) or m2.group(1).strip()

    plan_val = extract_plan(text)
    data.health_plan = plan_val
    data.contract_type = extract_contract(text)
    data.codes = extract_codes(text)
    data.change_request = extract_change_request(text)

    return data

