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
            print(f"Trying {domain}")
            _ = gethostbyname(f"{sub}.{domain}")
    except Exception:
        return False
    else:
        return True


def domain_sort(domain):
    return (not domain.startswith("wildcard."), domain.count("."), domain)


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

            for i in reversed(range(1, len(domain_by_dots) - 1)):
                maybe_wildcard = ".".join(domain_by_dots[i:])
                print(maybe_wildcard)
                if maybe_wildcard not in possible_wildcards:
                    possible_wildcards.add(maybe_wildcard)


possible_wildcards = sorted(possible_wildcards, key=lambda x: x.count("."))
print("Possible wildcards: ", possible_wildcards)

# Filter out static DNS wildcards
for maybe_wildcard in possible_wildcards:
    if not is_wildcard(maybe_wildcard):
        continue
    orig_len = len(domains)
    domains = set(d for d in domains if not d.endswith(f".{maybe_wildcard}"))
    if orig_len != len(domains):
        domains.add(f"wildcard.{maybe_wildcard}")

with ThreadPoolExecutor() as executor:
    for domain in domains:
        future = executor.submit(task, (domain))

with open(sys.argv[1], "w") as out:
    out.write("\n".join(sorted(resolvable, key=domain_sort)))

# Replace resolvable with domains for more results (but more false positives)
with open(sys.argv[2], "w") as out_domains:
    out_domains.write(
        "\n".join((sorted((r.split(",")[0] for r in resolvable), key=domain_sort)))
    )
