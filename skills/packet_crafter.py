from core.skills.registry import tool


@tool()
def craft_arp(target_ip: str, target_mac: str = "ff:ff:ff:ff:ff:ff", iface: str = "") -> str:
    """Craft and send an ARP packet using Scapy."""
    try:
        from scapy.all import ARP, Ether, sendp
        pkt = Ether(dst=target_mac) / ARP(pdst=target_ip)
        kwargs = {}
        if iface:
            kwargs["iface"] = iface
        sendp(pkt, count=1, verbose=False, **kwargs)
        return "Sent ARP request to {} via {}".format(target_ip, iface or "default interface")
    except ImportError:
        return "Scapy not available"
    except PermissionError:
        return "Permission denied (need root for raw sockets)"
    except Exception as e:
        return f"Error: {e}"


@tool()
def craft_dns(domain: str, query_type: str = "A", server: str = "8.8.8.8") -> str:
    """Craft and send a DNS query using Scapy."""
    try:
        from scapy.all import DNS, DNSQR, IP, UDP, sr1
        pkt = IP(dst=server) / UDP(sport=12345, dport=53) / DNS(rd=1, qd=DNSQR(qname=domain, qtype=query_type))
        reply = sr1(pkt, timeout=3, verbose=False)
        if reply and reply.haslayer(DNS):
            answers = reply[DNS].an
            if not answers:
                return f"No DNS answers for {domain}"
            results = []
            for i in range(getattr(answers, 'count', 1)):
                try:
                    val = answers[i].rdata
                    results.append(val.decode() if isinstance(val, bytes) else str(val))
                except Exception:
                    results.append(str(answers))
            return "DNS {} query for {}: {}".format(query_type, domain, ", ".join(results[:10]))
        return f"No DNS response from {server}"
    except ImportError:
        return "Scapy not available"
    except Exception as e:
        return f"Error: {e}"


@tool()
def craft_http(host: str, method: str = "GET", path: str = "/", port: int = 80) -> str:
    """Craft and send a raw HTTP request via raw socket."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        request = f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode())
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        sock.close()
        try:
            body = response.decode("utf-8", errors="replace")
        except Exception:
            body = response.hex()[:500]
        return "HTTP %s %s:%d%s\n---\n%s" % (method, host, port, path, body[:2000])
    except OSError as e:
        return f"Socket error: {e}"
    except Exception as e:
        return f"Error: {e}"
