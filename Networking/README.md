# Networking Fundamentals for DevOps

Practical networking notes for operating Linux servers, cloud workloads, containers, and Kubernetes. Examples use common Linux tools; some commands may need `sudo` or package installation (`iproute2`, `dnsutils`/`bind-utils`, `curl`, `traceroute`/`tracepath`, `tcpdump`, `mtr`). Run packet captures and changes only on systems and networks you are authorized to troubleshoot.

## Learning path

1. Understand IP addresses, CIDR, subnets, gateways, and routes.
2. Learn how DNS, TCP/UDP, ports, TLS, and HTTP fit together.
3. Inspect interfaces, routes, sockets, and firewall policy.
4. Troubleshoot from the client toward the service, changing one layer at a time.
5. Practice with the production incident examples below.

## 1. Networking fundamentals

### The request path

A typical web request follows this path:

```text
Client -> DNS lookup -> destination IP -> route/gateway -> firewall/security policy
       -> load balancer/reverse proxy -> service listener -> application -> response
```

If a request fails, determine the last step that succeeds. A successful DNS lookup does not prove that a TCP connection works; a successful TCP connection does not prove that TLS or the application is healthy.

### OSI model as a troubleshooting guide

| Layer | What it covers | Example checks |
| --- | --- | --- |
| 7 Application | HTTP, DNS, SSH, application behavior | `curl -v`, application logs, `dig` |
| 6 Presentation | Encoding and encryption, commonly TLS | `openssl s_client`, certificate inspection |
| 5 Session | Dialogs and connection state | Application/session logs |
| 4 Transport | TCP/UDP, ports, retransmits | `ss`, `nc`, `tcpdump` |
| 3 Network | IP addressing and routing | `ip addr`, `ip route`, `ping`, `traceroute` |
| 2 Data link | Ethernet, MAC, VLAN, neighbor discovery | `ip link`, `ip neigh` |
| 1 Physical | Link, cabling, radio, interface carrier | `ip link`, platform/hypervisor status |

The model is a diagnostic aid; real systems do not always map cleanly to one layer.

### IP addresses and CIDR

An IP address identifies an interface on an IP network. IPv4 looks like `192.0.2.10`; IPv6 looks like `2001:db8::10`. CIDR notation adds the number of network bits, such as `192.0.2.0/24` (256 total IPv4 addresses, with usable host count depending on the network design). Smaller prefix numbers describe larger networks: `/16` is larger than `/24`.

- A host uses its subnet mask/prefix to decide whether a destination is local.
- Traffic for another network is sent to a default gateway (router).
- Private IPv4 ranges include `10.0.0.0/8`, `172.16.0.0/12`, and `192.168.0.0/16`; they are not directly routed across the public internet.
- Loopback is `127.0.0.1` (IPv4) or `::1` (IPv6). It refers to the local host, not another machine.
- Link-local IPv4 (`169.254.0.0/16`) often indicates DHCP or address configuration trouble, though cloud platforms may use it for metadata services.

Example: for `10.20.3.14/24`, the local network is `10.20.3.0/24`. A destination such as `10.20.3.50` is local; `10.20.4.50` normally goes through a router.

### Routing

The routing table selects the next hop for a destination. More specific routes usually win over less specific routes; the default route (`0.0.0.0/0` or `::/0`) is used when no more-specific route matches. Asymmetric routing (request and response taking different paths) can break stateful firewalls and load balancers.

### TCP, UDP, and ports

- TCP is connection-oriented and provides ordered, retransmitted byte streams. HTTPS, SSH, and most database connections use TCP.
- UDP sends independent datagrams without TCP's delivery guarantees. DNS commonly uses UDP and may use TCP; voice, streaming, and some service discovery use UDP.
- A port identifies a service endpoint on a host. A listening server port is not the same as a client-side ephemeral port.
- `0.0.0.0` means listen on all IPv4 interfaces; `127.0.0.1` means local IPv4 only. `::` and `::1` are the IPv6 equivalents. A service bound only to loopback cannot be reached remotely.

Common ports: SSH 22/TCP, DNS 53/UDP and TCP, HTTP 80/TCP, HTTPS 443/TCP, NTP 123/UDP, PostgreSQL 5432/TCP, MySQL 3306/TCP. Confirm actual service configuration rather than assuming defaults.

### DNS

DNS maps names to records, including A (IPv4), AAAA (IPv6), CNAME (alias), MX (mail), and TXT (text/verification). A resolver may cache answers for the record's TTL. Check the record, resolver path, search domains, and both IPv4 and IPv6 answers when behavior differs by client.

### HTTP and TLS

HTTP runs over a transport connection; HTTPS adds TLS encryption and certificate identity checks. A TCP connection can succeed while TLS fails due to an expired/mismatched certificate, unsupported protocol, or missing intermediate certificate. An HTTP status such as 404 or 503 proves that some HTTP server answered, but does not by itself identify whether the response came from a proxy or the application.

### Firewalls and load balancers

Traffic can be filtered at multiple points: host firewall, cloud security groups/firewall rules, network ACLs, Kubernetes network policies, and load balancer rules. Check both ingress and egress, protocol, port, and source/destination CIDR. A load balancer also has health checks, listeners, target registration, and routing rules that must agree with the backend service.

## 2. Frequently used networking commands

### Interface, address, route, and neighbor inspection

```bash
ip -br addr                         # Compact interface/address view
ip addr show                        # Detailed IPv4 and IPv6 addresses
ip link show                        # Link state and interface details
ip route                            # IPv4 routing table
ip -6 route                         # IPv6 routing table
ip route get 1.1.1.1                # Route and source address selected for a destination
ip neigh                            # Neighbor/ARP cache on the local network
hostname -I                         # Addresses assigned to this host
```

### DNS and name resolution

```bash
getent ahosts example.com           # Check name lookup using system resolver config
dig example.com                     # Query DNS records using configured resolver
dig A example.com                   # IPv4 record
dig AAAA example.com                # IPv6 record
dig @1.1.1.1 example.com            # Query a specific resolver
dig +trace example.com              # Follow delegation from DNS root
cat /etc/resolv.conf                # Inspect resolver configuration (may be managed)
```

`getent` reflects the host's configured name service path; `dig` queries DNS directly. If they disagree, inspect `/etc/nsswitch.conf`, local caches, search domains, and resolver configuration.

### Reachability, ports, and HTTP/TLS

```bash
ping -c 4 1.1.1.1                   # Basic IP reachability/latency; ICMP may be filtered
tracepath example.com               # Discover path/MTU clues (if installed)
traceroute example.com              # Show hops; intermediate hops may not reply
mtr -rw example.com                 # Repeated route/packet-loss view (if installed)
nc -vz -w 3 example.com 443         # Test a TCP port (netcat syntax varies)
curl -v --connect-timeout 5 https://example.com/  # DNS, connect, TLS, and HTTP details
curl -sS -o /dev/null -w '%{http_code} %{remote_ip} %{time_namelookup} %{time_connect} %{time_appconnect} %{time_total}\n' https://example.com/
openssl s_client -connect example.com:443 -servername example.com </dev/null # Inspect TLS handshake/certificate chain
```

Ping and traceroute use ICMP or probe packets that networks may filter or deprioritize. A failed ping alone does not prove a service is down.

### Listening sockets and active connections

```bash
ss -lntp                             # Listening TCP sockets and process (root may show all PIDs)
ss -lnup                             # Listening UDP sockets
ss -ant                              # TCP sockets and states
ss -s                                # Socket summary
sudo lsof -nP -i                     # Processes using network sockets (if installed)
```

### Packet capture

```bash
sudo tcpdump -ni any host 10.0.1.25 and port 443
sudo tcpdump -ni eth0 'tcp port 8080' -c 100
```

Captures can contain credentials or customer data. Filter narrowly, restrict access to capture files, and stop as soon as the needed evidence is collected.

### Firewall checks (read-only examples)

```bash
sudo ufw status verbose                 # Ubuntu systems using UFW
sudo nft list ruleset                   # nftables rules
sudo iptables -S                        # iptables rule listing (legacy or compatibility layer)
```

Do not assume all tools represent the active firewall backend. Cloud firewalls and network policies are configured outside the host and must be checked in their respective control planes.

## 3. A practical troubleshooting workflow

Use the same destination, source, protocol, and time window when comparing results.

1. **Define the failure.** Record the client, URL/IP, port, start time, scope (one host, one subnet, all users), and exact error. Check whether a recent deploy, DNS, firewall, certificate, or routing change occurred.
2. **Check the service locally.** Confirm the process and listener (`systemctl status SERVICE`, `ss -lntp`). Test the local endpoint with `curl` or `nc`.
3. **Check address and route.** Inspect `ip addr`, `ip route`, and `ip route get DESTINATION`. Confirm the chosen source address and gateway are expected.
4. **Check DNS.** Compare `getent ahosts NAME`, `dig A NAME`, and `dig AAAA NAME`; query a known resolver if needed. Compare answers from a working and failing client.
5. **Check transport.** Test the exact port with `nc -vz`; use `curl -v` to distinguish name lookup, connection, TLS, and HTTP failures. Validate the path with `tracepath`/`mtr` where available.
6. **Check policy and middleboxes.** Review host firewalls, cloud security rules, ACLs, network policies, proxies, load balancer listeners and target health. Verify both directions and the real source CIDR after NAT.
7. **Collect evidence at both ends.** Use timestamps, service/proxy logs, connection counters, and a short filtered `tcpdump` to determine whether SYNs arrive and whether replies leave.
8. **Make the smallest reversible correction.** Change one rule or setting, re-test from the same source, and monitor. Record the change and rollback path.

Useful interpretations:

- **Connection refused:** The destination was reachable, but nothing accepted that port or a firewall actively rejected it. Check listener address/port and local reject rules.
- **Timeout:** Packets or replies may be dropped, the service may be stalled, or a path may be broken. Check each firewall/routing hop and capture at both endpoints.
- **No route to host:** Check local routes, gateway, subnet configuration, and host/network unreachable responses.
- **Name resolution failure:** Investigate resolver reachability, record contents, search domains, and cache/TTL.
- **TLS/certificate error:** Check hostname/SNI, validity dates, trust chain, and the certificate served by the actual load balancer/proxy.
- **HTTP 5xx:** Identify which layer generated the response; inspect load balancer/proxy and application health and logs.

## 4. Common production incidents and fixes

| Symptom | Likely checks | Typical resolution |
| --- | --- | --- |
| Users cannot reach a service; host responds locally | `ss -lntp`, `ip route`, host and cloud firewall rules; test from inside and outside the subnet | Start/fix the service listener; bind to the intended interface; allow only the required source CIDR and port through every policy layer; correct the route or gateway. |
| Port is open on the host but clients time out | Compare host capture with client test; check security groups, network ACLs, Kubernetes policy, NAT and return route | Permit the intended flow in both directions and fix asymmetric/missing return routing. Verify the real source after NAT. |
| Service reports “connection refused” | `ss -lntp`, service status/logs, destination IP and port | Start the service, correct its port/bind address, or update the client/proxy target to the actual listener. Avoid opening firewall ports when no service is listening. |
| DNS intermittently resolves to the wrong address | `dig` from multiple resolvers/clients; inspect A/AAAA/CNAME, TTL, split-horizon zones and local caches | Correct the authoritative record or private/public zone, account for cached TTL, and flush only the affected resolver/client cache when appropriate. Check stale AAAA records as well as A records. |
| Works by IPv4 but fails for some users | `dig A`/`dig AAAA`, `curl -4` and `curl -6`, IPv6 route and listener | Configure IPv6 routing, firewall, and service listener correctly, or remove an unintended AAAA record until IPv6 is supported. |
| HTTPS fails after certificate renewal | `openssl s_client -connect HOST:443 -servername HOST`, expiry/hostname/chain inspection, proxy/LB configuration | Install the correct certificate and full chain at the TLS termination point, include the right SAN and SNI mapping, then reload safely and verify externally. |
| Load balancer returns 502/503 or marks every target unhealthy | Listener/rule, target health reason, health-check path/port/protocol, backend bind address, security rules | Make the health endpoint return the expected code; align health-check and backend ports; allow LB-to-target traffic; restore backend capacity. Do not weaken health checks without understanding the failure. |
| Requests are slow or intermittently time out | `mtr`/`ss -ti`, `curl` timing fields, packet loss/retransmits, CPU/memory, conntrack and LB metrics | Locate where latency starts; address congestion, packet loss, overloaded service, MTU/PMTUD issues, or connection-pool exhaustion based on measurements. Avoid blindly increasing timeouts. |
| Large uploads, TLS handshakes, or VPN traffic stall | `tracepath`, interface MTU, filtered packet capture, ICMP “fragmentation needed”/Packet Too Big handling | Correct MTU/MSS and permit necessary path-MTU signaling; verify end-to-end. Avoid lowering MTU broadly without evidence. |
| New deployments exhaust connections or ephemeral ports | `ss -s`, `ss -ant`, TIME-WAIT counts, app connection-pool and NAT/conntrack metrics | Fix connection reuse and pool limits, close leaked sockets, scale/adjust NAT or conntrack capacity where supported, and apply OS tuning only after confirming the bottleneck. |
| Container can reach service by IP but not by name | Container DNS config, resolver reachability, Docker/Kubernetes DNS and network policy | Fix the container DNS/service name, cluster DNS health, or egress policy; use service discovery names rather than short-lived container IPs. |
| SSH access lost after a network change | Out-of-band console, route and firewall changes, cloud security rules, `sshd` listener | Recover through the provider console, restore the known-good route/rule, validate a second SSH session before closing the first, and keep a rollback path for future changes. |

Production changes should be narrow and observable: preserve current access, capture the before state, change one variable, confirm from a representative client, and revert if the expected signal does not improve.

## 5. Quick command checklist

For a web endpoint at `https://app.example.com`:

```bash
getent ahosts app.example.com
dig A app.example.com
dig AAAA app.example.com
ip route get <resolved-ip>
nc -vz -w 3 app.example.com 443
curl -v --connect-timeout 5 https://app.example.com/
openssl s_client -connect app.example.com:443 -servername app.example.com </dev/null
```

On the server, check the listener, policy, logs, and traffic:

```bash
ip -br addr
ip route
ss -lntp
sudo ufw status verbose               # If UFW is used
sudo journalctl -u <service> -n 100 --no-pager
sudo tcpdump -ni any 'host <client-ip> and port 443' -c 100
```

## Practice exercises

1. Inspect your interface addresses, routes, and neighbor table. Identify the default route and source address selected for an external destination.
2. Compare `getent ahosts example.com` with `dig A` and `dig AAAA`; explain which resolver each command uses.
3. Run a local HTTP server in a VM, confirm its listener with `ss`, and test it with `curl` from localhost and another authorized host.
4. Use `curl -v` and `openssl s_client` to inspect an HTTPS connection and certificate.
5. In a disposable lab, block one test port and compare the client behavior for a dropped connection versus a rejected connection.
6. Write a short incident note with symptom, scope, evidence, root cause, fix, and prevention.

Use a lab or an authorized system for experiments. For related host administration commands, see the [Linux guide](../Linux/README.md); for cloud networking, see the [AWS guide](../AWS/README.md).
