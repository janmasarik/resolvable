import sys
import contextlib
import random
import string

from socket import gethostbyname
from concurrent.futures import ThreadPoolExecutor

resolvable = []
domains = set()
possible_wildcards = set()


def task(domain):
    with contextlib.suppress(Exception):
        ip = gethostbyname(domain)
        resolvable.append(f"{domain},{ip}")


def is_wildcard(domain):
    try:
        for sub in (
            "".join(random.choices(string.ascii_lowercase, k=10)),
            "plznoresults",
            "gibbountyplz",
        ):
            _ = gethostbyname(f"{sub}.{domain}")
    except Exception:
        return False
    else:
        return True


# load domains from all sources into domains set
for file_name in sys.argv[3:]:
    with open(file_name) as domains_file:
        for line in domains_file:
            domain = line.strip().lower()
            if not domain:
                continue

            # Fix domains startnig with .
            if domain[0] == ".":
                domain = domain[1:]

            domains.add(domain)

            domain_by_dots = domain.split(".")
            if len(domain_by_dots) <= 2:
                continue

            for i in range(len(domain_by_dots) - 2):
                print(".".join(domain_by_dots[i:]))
                possible_wildcards.add(".".join(domain_by_dots[i:]))


possible_wildcards = sorted(possible_wildcards, key=lambda item: item.count("."))
# Filter out static DNS wildcards
for maybe_wildcard in possible_wildcards:
    if is_wildcard(maybe_wildcard):
        orig_len = len(domains)
        domains = set(d for d in domains if not d.endswith(maybe_wildcard))
        if orig_len != len(domains):
            domains.add(f"wildcard.{maybe_wildcard}")

with ThreadPoolExecutor() as executor:
    for domain in domains:
        future = executor.submit(task, (domain))

with open(sys.argv[1], "w") as out:
    out.write("\n".join(sorted(resolvable)))

with open(sys.argv[2], "w") as out_domains:
    out_domains.write("\n".join(sorted(domains)))
