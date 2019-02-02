import sys
import contextlib

from socket import gethostbyname
from concurrent.futures import ThreadPoolExecutor

resolvable = []
domains = set()


def task(domain):
    with contextlib.suppress(Exception):
        ip = gethostbyname(domain)
        resolvable.append(f"{domain},{ip}")


# load domains from all sources into domains set
for file_name in sys.argv[3:]:
    with open(file_name) as domains_file:
        for line in domains_file:
            domain = line.strip().lower()
            if domain:
                domains.add(domain)

with ThreadPoolExecutor() as executor:
    for domain in domains:
        future = executor.submit(task, (domain))

with open(sys.argv[1], "w") as out:
    out.write("\n".join(sorted(resolvable)))

with open(sys.argv[2], "w") as out_domains:
    out_domains.write("\n".join(sorted(domains)))
