# logslice

Fast log filtering utility that supports structured and unstructured log formats.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

Filter logs by level, time range, or keyword:

```bash
# Filter by log level
logslice --level ERROR app.log

# Filter by time range
logslice --from "2024-01-15 10:00:00" --to "2024-01-15 11:00:00" app.log

# Filter structured (JSON) logs by field value
logslice --field service=auth --level WARN app.log

# Pipe from stdin
cat app.log | logslice --keyword "connection refused"
```

Python API:

```python
from logslice import LogSlicer

slicer = LogSlicer("app.log")
results = slicer.filter(level="ERROR", keyword="timeout")

for entry in results:
    print(entry)
```

---

## Supported Formats

- Plain text / unstructured logs
- JSON (newline-delimited)
- Common log formats (Apache, Nginx, syslog)

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE)