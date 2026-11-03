"""hooks/_lib/hosts.py — which host names mean "this machine", for every component that gates traffic.

Born 2026-10-30 (implementation-layer SSOT scan, AP-74) by MERGING two hand copies that had drifted:
`hooks/browser_pane_scope_guard.py` (LOCAL_HOSTS with `0.0.0.0`) and `tools/page-fill-gate/fill_gate.py`
(LOCAL_HOSTS without it). The set is their union: `0.0.0.0` is what `python -m http.server` prints as
its address and it reaches this machine, never the network.

Consumers: browser_pane_scope_guard (a host string from a URL the pane is about to open) and
fill_gate (the route filter that lets a built page load its own loopback assets). Shared cases:
`hooks/tests/test_hosts.py` runs both consumers over HOST_CASES.
"""

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"})


def is_local_host(host: str) -> bool:
    """A lower-cased host name that resolves to this machine (exact name, or a *.localhost name)."""
    if not isinstance(host, str):
        return False   # undetermined input (None, bytes, a parse failure): never "local"
    host = host.lower()
    return host in LOCAL_HOSTS or host.endswith(".localhost")


# (host, local?) — run by every consumer's suite; a consumer that answers differently is the defect
HOST_CASES = (
    ("localhost", True), ("127.0.0.1", True), ("0.0.0.0", True), ("::1", True), ("[::1]", True),
    ("site.localhost", True),
    ("localhost.evil.com", False), ("example.com", False), ("10.0.0.5", False), ("", False),
    ("127.0.0.2", False),
)
