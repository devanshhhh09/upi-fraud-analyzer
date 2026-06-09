import re
import socket
import requests
import datetime
import tldextract
from pathlib import Path
from src.utils.logger import get_logger
import config

logger = get_logger(__name__)

URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
    'short.link', 'cutt.ly', 'rb.gy', 'tiny.cc', 'is.gd',
}

SUSPICIOUS_TLDS = {
    'tk', 'ml', 'ga', 'cf', 'gq',
    'xyz', 'top', 'club', 'online', 'site',
    'work', 'click', 'link', 'live', 'stream',
}

HIGH_RISK_REGISTRARS = {
    'namecheap', 'godaddy', 'hostinger',
    'reg.ru', 'nicenic', 'west263',
}

IMPERSONATION_TARGETS = [
    'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'pnb', 'bob',
    'paytm', 'phonepe', 'gpay', 'googlepay', 'bhim',
    'uidai', 'aadhaar', 'irctc', 'incometax', 'epfo',
    'npci', 'upi', 'rbi', 'sebi', 'nic', 'gov',
    'amazon', 'flipkart', 'meesho', 'swiggy', 'zomato',
]


def extract_domain(url):
    url = str(url).strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    extracted = tldextract.extract(url)
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"
    return url


def whois_lookup(domain):
    result = {
        'domain':          domain,
        'registrar':       'Unknown',
        'creation_date':   None,
        'expiry_date':     None,
        'domain_age_days': None,
        'country':         'Unknown',
        'status':          'Unknown',
        'error':           None,
    }
    try:
        import whois
        w = whois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation:
            if isinstance(creation, str):
                creation = datetime.datetime.strptime(creation[:10], '%Y-%m-%d')
            result['creation_date']   = str(creation)[:10]
            result['domain_age_days'] = (datetime.datetime.now() - creation).days
        expiry = w.expiration_date
        if isinstance(expiry, list):
            expiry = expiry[0]
        if expiry:
            result['expiry_date'] = str(expiry)[:10]
        result['registrar'] = str(w.registrar or 'Unknown')[:60]
        result['country']   = str(w.country or 'Unknown')
        result['status']    = (w.status[0] if isinstance(w.status, list) else str(w.status or ''))[:50]
        logger.info(f"WHOIS {domain}: age={result['domain_age_days']} days")
    except Exception as e:
        result['error'] = str(e)[:100]
        logger.warning(f"WHOIS failed for {domain}: {e}")
    return result


def dns_lookup(domain):
    result = {
        'domain':       domain,
        'ip_addresses': [],
        'resolvable':   False,
        'error':        None,
    }
    try:
        ips = socket.getaddrinfo(domain, None)
        result['ip_addresses'] = list({addr[4][0] for addr in ips})
        result['resolvable']   = True
        logger.info(f"DNS {domain}: {result['ip_addresses']}")
    except Exception as e:
        result['error'] = str(e)[:100]
        logger.warning(f"DNS lookup failed for {domain}: {e}")
    return result


def check_brand_impersonation(domain):
    domain_lower = domain.lower()
    extracted    = tldextract.extract(domain_lower)
    domain_part  = extracted.domain
    impersonated = []
    for brand in IMPERSONATION_TARGETS:
        if brand in domain_part and domain_part != brand:
            impersonated.append(brand)
        if _levenshtein(domain_part, brand) == 1 and len(brand) > 3:
            impersonated.append(f"{brand} (typosquat)")
    return {
        'impersonates':     list(set(impersonated)),
        'is_impersonation': len(impersonated) > 0,
    }


def _levenshtein(s1, s2):
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = range(len(s2) + 1)
    for c1 in s1:
        curr    = [0] * (len(s2) + 1)
        curr[0] = prev[0] + 1
        for j, c2 in enumerate(s2):
            curr[j+1] = min(prev[j] + (c1 != c2), curr[j] + 1, prev[j+1] + 1)
        prev = curr
    return prev[len(s2)]


def calculate_risk_score(whois_data, dns_data, impersonation_data, domain):
    score      = 0
    indicators = []
    extracted  = tldextract.extract(domain)
    tld        = extracted.suffix.lower()

    age = whois_data.get('domain_age_days')
    if age is None:
        score += 20
        indicators.append("WHOIS data unavailable — privacy shield likely")
    elif age < 30:
        score += 35
        indicators.append(f"Domain very new — only {age} days old")
    elif age < 90:
        score += 20
        indicators.append(f"Domain recently created — {age} days old")
    elif age < 365:
        score += 10
        indicators.append(f"Domain less than 1 year old — {age} days")

    if tld in SUSPICIOUS_TLDS:
        score += 20
        indicators.append(f"Suspicious TLD: .{tld}")

    if domain in URL_SHORTENERS:
        score += 25
        indicators.append("URL shortener — hides real destination")

    if impersonation_data['is_impersonation']:
        score += 30
        brands = ', '.join(impersonation_data['impersonates'])
        indicators.append(f"Impersonates known brand: {brands}")

    if not dns_data['resolvable']:
        score += 15
        indicators.append("Domain does not resolve — possibly taken down")

    registrar = whois_data.get('registrar', '').lower()
    for hr in HIGH_RISK_REGISTRARS:
        if hr in registrar:
            score += 10
            indicators.append(f"Registrar associated with fraud domains: {registrar[:40]}")
            break

    score      = min(score, 100)
    risk_level = (
        'CRITICAL' if score >= 75 else
        'HIGH'     if score >= 50 else
        'MEDIUM'   if score >= 25 else
        'LOW'
    )
    return {'score': score, 'risk_level': risk_level, 'indicators': indicators}


def analyze_domain(url):
    domain        = extract_domain(url)
    logger.info(f"Analyzing domain: {domain}")
    whois_data    = whois_lookup(domain)
    dns_data      = dns_lookup(domain)
    impersonation = check_brand_impersonation(domain)
    risk          = calculate_risk_score(whois_data, dns_data, impersonation, domain)
    return {
        'url':           url,
        'domain':        domain,
        'whois':         whois_data,
        'dns':           dns_data,
        'impersonation': impersonation,
        'risk':          risk,
    }


def format_report(analysis):
    w   = analysis['whois']
    d   = analysis['dns']
    r   = analysis['risk']
    imp = analysis['impersonation']
    lines = [
        "=" * 55,
        "THREAT INTELLIGENCE REPORT",
        "=" * 55,
        f"URL:          {analysis['url']}",
        f"Domain:       {analysis['domain']}",
        "",
        "── WHOIS INFORMATION ──────────────────────────────",
        f"Registrar:    {w['registrar']}",
        f"Created:      {w['creation_date'] or 'Unknown'}",
        f"Expires:      {w['expiry_date'] or 'Unknown'}",
        f"Domain age:   {w['domain_age_days']} days" if w['domain_age_days'] else "Domain age:   Unknown",
        f"Country:      {w['country']}",
        "",
        "── DNS INFORMATION ────────────────────────────────",
        f"Resolvable:   {d['resolvable']}",
        f"IP addresses: {', '.join(d['ip_addresses']) or 'None'}",
        "",
        "── BRAND IMPERSONATION ────────────────────────────",
        f"Detected:     {imp['is_impersonation']}",
        f"Targets:      {', '.join(imp['impersonates']) or 'None'}",
        "",
        "── RISK ASSESSMENT ────────────────────────────────",
        f"Risk score:   {r['score']}/100",
        f"Risk level:   {r['risk_level']}",
        "",
        "Risk indicators:",
    ]
    for indicator in r['indicators']:
        lines.append(f"  ⚠ {indicator}")
    if not r['indicators']:
        lines.append("  ✓ No risk indicators found")
    lines.append("=" * 55)
    return "\n".join(lines)


if __name__ == "__main__":
    test_urls = [
        "https://sbi-kyc-update.xyz",
        "https://www.google.com",
        "https://hdfc-bank-verify.tk",
        "https://paytm-reward-claim.online",
    ]
    for url in test_urls:
        print(f"\nAnalyzing: {url}")
        analysis = analyze_domain(url)
        print(format_report(analysis))
