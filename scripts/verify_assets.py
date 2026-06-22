#!/usr/bin/env python3
"""
verify_assets.py — Registry vs Realidad para assets/.

Cruza el campo `network` de cada asset contra evidencia viva:
- ping (¿host vivo?)
- ip neigh (¿MAC en ARP table?)
- /sys/class/net/*/address (¿MAC real del OS?)
- uname -n via SSH (¿hostname real?)

Output: tabla con discrepancias + lista de YAMLs a patchear.

Uso:
    python3 verify_assets.py                    # local-only check
    python3 verify_assets.py --ssh              # también consulta por SSH hosts remotos
    python3 verify_assets.py --hosts 192.168.1.52,192.168.1.54  # override hosts

Compañero de verify_ports.py. Mismo principio: ningún claim del Registry es
autoritativo hasta ser verificado contra red real.
"""

import sys
import os
import subprocess
import argparse

sys.path.insert(0, '/home/carlos/.hermes/skills/registry')
from registry import registry_list, registry_get


# ===== Evidence collection =====

def ping(ip, timeout=2):
    """True si el host responde a ICMP."""
    if not ip or ip == '—':
        return False
    try:
        r = subprocess.run(
            ['ping', '-c', '1', '-W', str(timeout), ip],
            capture_output=True, text=True, timeout=timeout + 2
        )
        return r.returncode == 0 and 'from' in r.stdout
    except Exception:
        return False


def arp_mac(ip):
    """Extrae MAC de `ip neigh` para una IP. None si no está (FAILED o ausente)."""
    try:
        r = subprocess.run(['ip', 'neigh', 'show', ip], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[2] == 'lladdr':
                return parts[4].lower()
    except Exception:
        pass
    return None


def ssh_query(ip, cmd):
    """Ejecuta cmd por SSH. None si no se puede conectar."""
    try:
        r = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=3', '-o', 'BatchMode=yes', f'carlos@{ip}', cmd],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def local_mac():
    """MAC de la NIC uplink default (la que sale a la LAN)."""
    try:
        r = subprocess.run(['ip', 'route', 'show', 'default'],
                           capture_output=True, text=True)
        iface = None
        for line in r.stdout.splitlines():
            parts = line.split()
            if 'dev' in parts:
                iface = parts[parts.index('dev') + 1]
                break
        if not iface:
            for cand in ['end0', 'eth0', 'eno1']:
                if os.path.exists(f'/sys/class/net/{cand}'):
                    iface = cand
                    break
        if not iface:
            return None
        with open(f'/sys/class/net/{iface}/address') as f:
            return f.read().strip().lower()
    except Exception:
        return None


def local_ip():
    try:
        r = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        parts = r.stdout.split()
        return parts[0] if parts else None
    except Exception:
        return None


# ===== Discrepancy detection =====

# MACs que son claramente placeholders / defaults de VM
PLACEHOLDER_MACS = {
    '52:54:00:12:34:56', '52:54:00:00:00:00',       # QEMU/libvirt default
    '02:42:ac:11:00:00', '02:42:ac:11:00:01',       # Docker bridge default
}


def is_placeholder_mac(mac):
    if not mac:
        return True
    return mac.lower() in PLACEHOLDER_MACS


def verify_assets(do_ssh=False, host_overrides=None):
    """Comparación Registry ↔ realidad. Retorna dict con stats y discrepancies."""
    my_ip = local_ip()
    my_mac = local_mac()

    # Realidad
    reality = {}   # ip -> {live: bool, mac: str|None, hostname: str|None}
    candidates = []
    if host_overrides:
        candidates.extend(host_overrides)
    else:
        for a in registry_list('assets'):
            e = registry_get(a['id'])
            ip = e.get('network', {}).get('ip')
            if ip and ip != '—' and ip != my_ip:
                candidates.append(ip)

    for ip in candidates:
        live = ping(ip)
        mac = arp_mac(ip) if live else None
        hostname = None
        if do_ssh and live:
            hostname = ssh_query(ip, 'uname -n')

        reality[ip] = {
            'live': live,
            'mac': mac,
            'hostname': hostname,
        }

    # Incluir la máquina local
    if my_ip and my_ip not in reality:
        try:
            local_hostname = subprocess.run(['uname', '-n'], capture_output=True, text=True).stdout.strip()
        except Exception:
            local_hostname = None
        reality[my_ip] = {
            'live': True,
            'mac': my_mac,
            'hostname': local_hostname,
        }

    # Comparación
    discrepancies = []
    print('\n=== REGISTRY vs REALIDAD: ASSETS ===\n')
    print(f"{'Asset':22} | {'IP':16} | {'Registry MAC':18} | {'Reality MAC':18} | Status")
    print('-' * 95)

    for a in registry_list('assets'):
        e = registry_get(a['id'])
        net = e.get('network', {})
        ip = net.get('ip', '—')
        reg_mac = net.get('mac', '—')
        status = e.get('status', '—')
        rid = a['id']

        if ip == '—' or ip not in reality:
            print(f'{rid:22} | {ip:16} | {reg_mac:18} | {"—":18} | (no verificado)')
            continue

        real = reality[ip]
        real_mac_str = real['mac'] or 'no-neigh'

        # Detección de problemas
        issues = []
        if not real['live']:
            issues.append('WARN: ping FAIL')
        if status == 'operational' and not real['live']:
            issues.append('ERROR: status=operational pero host DOWN')
        if reg_mac == '—':
            issues.append('+ MAC no documentada')
        elif is_placeholder_mac(reg_mac):
            issues.append(f'ERROR: MAC placeholder ({reg_mac})')
        elif real['mac'] and reg_mac.lower() != real['mac']:
            issues.append(f'ERROR: MAC {reg_mac} != {real["mac"]}')

        flag = ' | '.join(issues) if issues else 'OK'
        if issues:
            discrepancies.append({'id': rid, 'ip': ip, 'issues': issues, 'real_mac': real['mac']})

        print(f'{rid:22} | {ip:16} | {reg_mac:18} | {real_mac_str:18} | {flag}')

    print(f'\nDiscrepancias encontradas: {len(discrepancies)}')
    for d in discrepancies:
        print(f"  {d['id']} ({d['ip']}):")
        for iss in d['issues']:
            print(f'    {iss}')
        if d['real_mac']:
            print(f'    Patch sugerido:    network.mac: "{d["real_mac"]}"')

    return {'discrepancies': discrepancies, 'reality': reality}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ssh', action='store_true', help='Consulta hostname por SSH (mas lento)')
    parser.add_argument('--hosts', type=str, help='CSV override de IPs a verificar')
    args = parser.parse_args()

    hosts = args.hosts.split(',') if args.hosts else None
    result = verify_assets(do_ssh=args.ssh, host_overrides=hosts)

    # Exit code != 0 si hay discrepancias (CI-friendly)
    sys.exit(1 if result['discrepancies'] else 0)
