import sys
import contextlib
import random
import string
import traceback
import dns.resolver

from socket import gethostbyname
from collections import namedtuple, defaultdict
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

resolvable = []
domains = set()
wildcard_domains = {}
DNSResponse = namedtuple("DNSResponse", ["type", "response"])
DNSRecord = namedtuple("DNSRecord", ["domain", "type", "response"])

# TODO WILDCARD CNAME
# TODO smart wildcard detection


def query(domain):
    response = {"CNAME": "", "AAAA": "", "A": ""}
    with contextlib.suppress(Exception):
        answers = dns.resolver.query(domain, "CNAME")
        response["CNAME"] = [str(answers[0].target)[:-1]]

    with contextlib.suppress(Exception):
        answers = dns.resolver.query(domain, "AAAA")
        response["AAAA"] = sorted(str(a) for a in answers)

    with contextlib.suppress(Exception):
        answers = dns.resolver.query(domain, "A")
        response["A"] = sorted(str(a) for a in answers)

    return response


def dns_record_sort(dns_record):
    return (
        dns_record.type != "CNAME",
        dns_record.response,
        dns_record.domain.count("."),
        dns_record.domain,
    )


def domain_sort(domain):
    return (domain.count("."), domain)


@lru_cache(maxsize=13370)
def get_wildcard_domain(domain):
    return query(f"{''.join(random.choices(string.ascii_lowercase, k=18))}.{domain}")


grouped_domains = defaultdict(list)
# load domains from massdns simple output
with open(sys.argv[3]) as domains_file:
    for line in domains_file:
        # kiwi.com. A 54.192.50.12
        # kiwi.com. A 54.192.50.75
        # kiwi.com. A 54.192.50.172
        # kiwi.com. A 54.192.50.107
        # kkkkkkk.skypicker.com. CNAME skypicker.com.
        # www.kiwi.com. CNAME www.kiwi.com.cdn.cloudflare.net.
        parsed_line = line.strip().lower().split(" ")
        if not parsed_line:
            continue

        parsed_line[0] = parsed_line[0][:-1]

        if parsed_line[1] == "cname" and parsed_line[2][-1] == ".":
            parsed_line[2] = parsed_line[2][:-1]

        grouped_domains[parsed_line[0]].append(
            DNSResponse(parsed_line[1], parsed_line[2])
        )

for domain, dns_responses in grouped_domains.items():
    if dns_responses[0].type == "cname":
        dns_record = DNSRecord(domain, "CNAME", tuple([dns_responses[0].response]))
    elif dns_responses[0].type == "a":
        dns_record = DNSRecord(domain, "A", tuple(sorted(a[1] for a in dns_responses)))
    else:
        print("Unexpected respone, dropping!", domain, dns_responses)

    domain_by_dots = dns_record.domain.split(".")

    for i in reversed(range(1, len(domain_by_dots) - 1)):
        maybe_wildcard = ".".join(domain_by_dots[i:])
        print(maybe_wildcard)
        wildcard_response = get_wildcard_domain(maybe_wildcard)
        print(wildcard_response)
        is_wildcard = False
        for wildcard_ip in wildcard_response[dns_record.type]:
            for ip in dns_record.response:
                if ip == wildcard_ip:
                    is_wildcard = True
                    break

        if is_wildcard:
            break

    else:
        resolvable.append(dns_record)

with open(sys.argv[1], "w") as out:
    for d in sorted(resolvable, key=dns_record_sort):
        responses_string = ", ".join(d.response)
        out.write(f"{d.domain} {d.type} {responses_string}\n")

with open(sys.argv[2], "w") as out_domains:
    for dom in sorted((d.domain for d in resolvable), key=domain_sort):
        out_domains.write(f"{dom}\n")
