#!/usr/bin/env python3
import sys
import re
import json
from pathlib import Path

F = Path(sys.argv[1])
content = F.read_text(encoding='utf-8')

checks = []

def add(id, name, line=-1):
    checks.append({"id": id, "name": name, "line": line})

# 1. Hardcoded secrets detection
if re.search(r"PAYMENT_TOKEN\s*=\s*\".*\"", content):
    add(1, "hardcoded_payment_token")
if re.search(r"MAIL_SERVER_KEY\s*=\s*\".*\"", content):
    add(2, "hardcoded_mail_key")
if re.search(r"INTERNAL_AUTH\s*=\s*\".*\"", content):
    add(3, "hardcoded_internal_auth")

# 2. SQL injection style pattern
if "%s'" in content or re.search(r"WHERE .*=%s", content) or "% uid" in content:
    add(10, "possible_sql_injection")

# 3. MD5 token usage
if re.search(r"hashlib\.md5\(", content):
    add(11, "md5_hashing_detected")

# 4. shell=True usage (command injection risk)
if re.search(r"subprocess\.[A-Za-z_]+\(.*shell\s*=\s*True", content):
    add(20, "shell_true_in_subprocess")

# 5. opening user-supplied path
if re.search(r"open\(path\)|open\(filename\)|open\(\w+\)", content) and re.search(r"request\.json", content):
    add(30, "file_read_from_user_input")

# 6. debug mode on
if re.search(r"app\.run\(.*debug\s*=\s*True", content):
    add(40, "debug_mode_enabled")

# 7. SSRF potential: requests.post to variable url
if re.search(r"requests\.post\(\s*url\W", content) or re.search(r"requests\.post\(.*notify_url", content):
    add(50, "possible_ssrf")

result = {"file": str(F), "issues": checks}
print(json.dumps(result, indent=2))

if checks:
    sys.exit(1)
else:
    sys.exit(0)
