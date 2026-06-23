from core.skills.registry import tool


@tool()
def generate_exploit_hypotheses(finding: str, code_snippet: str = "") -> str:
    """Given a security finding, formulate concrete exploit hypotheses and verification steps."""
    import textwrap
    hypotheses = []
    finding_lower = finding.lower()
    if "sql" in finding_lower and "injection" in finding_lower:
        hypotheses.append(textwrap.dedent("""\
        H1: SQL Injection via unsanitized input
          - Identify all user-controlled parameters reaching the query
          - Inject: ' OR 1=1 --
          - Verify: does the query return all rows?
          - Fix: parameterized queries / ORM
        """))
    if "xss" in finding_lower or "cross-site" in finding_lower or "script" in finding_lower:
        hypotheses.append(textwrap.dedent("""\
        H2: Stored/Reflected XSS
          - Identify user input rendered without escaping
          - Inject: <script>alert(1)</script>
          - Verify: does the script execute in the browser?
          - Fix: output encoding / CSP headers
        """))
    if "race" in finding_lower or "time-of-check" in finding_lower or "toctou" in finding_lower:
        hypotheses.append(textwrap.dedent("""\
        H3: TOCTOU race condition
          - Identify file operations that check before access
          - Send parallel requests to exploit the window
          - Verify: can state be corrupted?
          - Fix: atomic operations / file locking
        """))
    if "cache" in finding_lower or "stale" in finding_lower:
        hypotheses.append(textwrap.dedent("""\
        H4: Stale cache poisoning
          - Identify cached responses without TTL
          - Modify source data, observe stale value served
          - Verify: can old data be served to new requests?
          - Fix: add TTL / cache-busting keys
        """))
    if "auth" in finding_lower or "permission" in finding_lower or "privilege" in finding_lower:
        hypotheses.append(textwrap.dedent("""\
        H5: Privilege escalation
          - Access low-privilege endpoint, modify request to impersonate admin
          - Try: role=admin, user_id=1, is_admin=true
          - Verify: can low-priv user access admin resources?
          - Fix: server-side auth enforcement per endpoint
        """))
    if "injection" in finding_lower and "command" in finding_lower:
        hypotheses.append(textwrap.dedent("""\
        H6: Command injection
          - Identify system commands with user-controlled args
          - Inject: ; id ;  || id  | id
          - Verify: does output contain user/group info?
          - Fix: subprocess with args list, no shell=True
        """))
    if "path" in finding_lower and "traversal" in finding_lower:
        hypotheses.append(textwrap.dedent("""\
        H7: Path traversal
          - Identify file read endpoints with user-controlled paths
          - Inject: ../../../etc/passwd
          - Verify: can arbitrary files be read?
          - Fix: validate/restrict paths to allowed directory
        """))
    if not hypotheses:
        hypotheses.append(textwrap.dedent("""\
        H1: Investigate finding further
          - Review the code context around the finding
          - Identify attack surface: what can an attacker control?
          - Check for input validation, sanitization, encoding
          - Verify: can this finding be exploited in practice?
          - Classify: is the finding exploitable?
        """))
    result = f"=== Exploit Hypotheses for: {finding[:100]} ===\n"
    if code_snippet:
        result += f"\nRelevant code:\n{code_snippet[:500]}\n"
    result += "\n" + "\n".join(hypotheses)
    return result


@tool()
def generate_fuzzing_strategy(target_paths: str) -> str:
    """Given file paths (comma-separated), propose a fuzzing strategy."""
    import os
    paths = [p.strip() for p in target_paths.split(",")]
    inputs = []
    for p in paths:
        if os.path.isfile(p):
            inputs.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    inputs.append(os.path.join(root, f))
                if len(inputs) >= 50:
                    break
        if len(inputs) >= 50:
            break
    strategy = """=== Fuzzing Strategy ===
Input corpus: {count} files
Tools:        AFL++ / libFuzzer / Jazzer (Java) / go-fuzz
Instrumentation:
  - Compile with ASAN + UBSAN
  - Enable coverage-guided fuzzing
Mutation methods:
  - Bit flips, byte swaps, arithmetic increments
  - Dictionary insertion (known magic bytes)
  - Structure-aware mutations (if format known)
Targets:
  - Input parsers (JSON, XML, YAML, binary protocols)
  - URL/URI deserializers
  - Template rendering engines
  - SQL query builders
Crashes:
  - Collect and deduplicate by stack trace
  - Triage: exploitable vs. benign
  - Minimize each crash case
Duration: 24-48 hours minimum per target
"""
    return strategy.format(count=len(inputs))
