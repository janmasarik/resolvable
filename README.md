# Resolvable

- merge list of subdomains from various sources (domain per line)
- resolve them and output them sorted`domain,ip` to the file specified by sys.argv[1]
- `sort -u` of all domains to file specified by sys.argv[2]

## Usage
```python
docker run -v /data:/data s14ve/resolvable /data/resolved.txt /data/subdomains.txt /data/amass.txt /data/subfinder.txt
```