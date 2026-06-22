#!/usr/bin/env python3
"""
network_report.py — Query engine para Registry CIC

Genera reportes de red a partir del Registry sin intervención manual.

Uso:
  python3 scripts/network_report.py                  # resumen general
  python3 scripts/network_report.py --host 54        # servicios en .54 (resuelve numeric)
  python3 scripts/network_report.py --host 2         # servicios en POS
  python3 scripts/network_report.py --ports          # puertos expuestos
  python3 scripts/network_report.py --check          # ping sweep de todos los hosts
  python3 scripts/network_report.py --missing        # campos vacíos en assets
  python3 scripts/network_report.py --fingerprint    # comandos DNS/SSH sugeridos

IDES:
- Numeric matching: 54 → orange-pi-54, server-192-168-1-54
- Display ordenado por tipo, puertos agrupados por host
- Verificación de conectividad real (ping) antes de asumir status
"""

import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from registry import registry_list, registry_get, registry_validate

REGISTRY_DIR = os.path.expanduser("~/registry")
os.chdir(REGISTRY_DIR)


def print_separator():
    print("=" * 70)

def get_host_match(target):
    """Intenta encontrar un host por ID, IP parcial o nombre corto."""
    candidates = [target]
    if target.isdigit():
        candidates.append(f"192.168.1.{target}")
        candidates.append(f"server-192-168-1-{target}")
        candidates.append(f"orange-pi-{target}")
    for c in candidates:
        a = registry_get(c)
        if a:
            return a
    return None


def report_summary():
    """Reporte general: conteo por tipo, puertos expuestos, hosts down."""
    print_separator()
    print("  REGISTRY CIC — REPORTE DE RED")
    print_separator()
    print()

    # Conteos
    software = registry_list('software')
    assets = registry_list('assets')
    print(f"  Software registrados: {len(software)}")
    print(f"  Assets registrados:   {len(assets)}")
    print()

    # Agrupar por tipo
    by_type = {}
    for a in assets:
        e = registry_get(a['id'])
        t = e.get('type', 'unknown')
        by_type.setdefault(t, []).append(a['id'])
    
    print("  Tipo                      | Cant. | IDs")
    print("-" * 70)
    for t, ids in sorted(by_type.items()):
        id_str = ", ".join(ids[:3])
        if len(ids) > 3:
            id_str += f" ... y {len(ids)-3} más"
        print(f"  {t:24s}| {len(ids):5d} | {id_str}")
    print()

    # Puertos por host
    print("  PUERTOS EXPUESTOS EN RED")
    print("-" * 70)
    hosts_with_ports = {}
    for s in software:
        e = registry_get(s['id'])
        net = e.get('network', {})
        host_ip = net.get('host', '')
        port = net.get('port')
        if host_ip and port:
            hosts_with_ports.setdefault(host_ip, []).append((s['id'], port))
    
    for host_ip in sorted(hosts_with_ports.keys()):
        a = get_host_match(host_ip.split('.')[-1]) or {'name': host_ip}
        host_name = a.get('network', {}).get('hostname', host_ip)
        print(f"  {host_name:25s}({host_ip})")
        for sw_id, port in sorted(hosts_with_ports[host_ip], key=lambda x: x[1]):
            print(f"    ├─ {sw_id:20s}→ localhost:{port}")
    print()

    # Hosts no operacionales
    print("  HOSTS NO OPERACIONALES / PENDIENTES")
    print("-" * 70)
    for a in assets:
        e = registry_get(a['id'])
        status = e.get('status', 'unknown')
        if status in ['unknown', 'pending-identify', 'powered-off', 'construction']:
            ip = e.get('network', {}).get('ip', 'N/A')
            desc = e.get('description', '')[:60]
            print(f"  {a['id']:32s}| {status:18s}| {ip:16s}| {desc}")
    print()


def report_host(target):
    """Reporte detallado de un host específico."""
    a = get_host_match(target)
    if not a:
        print(f"Host '{target}' no encontrado.")
        print(f"Posibles hosts: {', '.join([x['id'] for x in registry_list('assets')][:20])}")
        return

    print_separator()
    print(f"  HOST: {a['id']:25s}({a.get('network', {}).get('ip', 'N/A')})")
    print_separator()
    
    mac = a.get('network', {}).get('mac', 'N/A')
    status = a.get('status', 'unknown')
    desc = a.get('description', '')
    print(f"  MAC:  {mac}")
    print(f"  Status: {status}")
    print(f"  Desc: {desc}")
    print()

    # Software corriendo en este host
    print("  SOFTWARE CORRIENDO:")
    sw_list = []
    deps = registry_get_dependencies(a['id']) if hasattr(registry_get, 'get_dependencies') else []
    
    # Buscar software con runs_on: [este_host]
    for s in registry_list('software'):
        e = registry_get(s['id'])
        relations = e.get('relations', {})
        runs_on = relations.get('runs_on', [])
        if a['id'] in runs_on or a.get('network', {}).get('ip') in [registry_get(r).get('network', {}).get('ip', '') for r in runs_on]:
            net = e.get('network', {})
            port = net.get('port', '—')
            url = f"http://{net.get('host', 'localhost')}:{port}" if port != '—' else '—'
            sw_list.append((s['id'], port, url))

    if sw_list:
        print(f"  Servicio             | Puerto   | URL/Acceso                              ")
        print("-" * 70)
        for sw_id, port, url in sorted(sw_list, key=lambda x: str(x[1])):
            print(f"  {sw_id:20s} | {str(port):8s} | {url}")
    else:
        print("  (no hay software corriendo en este host)")
    print()


def report_ports():
    """Lista todos los puertos expuestos, agrupados por host."""
    print_separator()
    print("  PUERTOS EXPUESTOS — TODOS LOS HOSTS")
    print_separator()
    report_summary()  # reusar la sección de puertos del summary


def report_check():
    """Ping sweep de todos los hosts del Registry."""
    print_separator()
    print("  CHECK DE CONECTIVIDAD — PING SWEEP")
    print_separator()
    print()

    results = []
    for a in registry_list('assets'):
        ip = a.get('network', {}).get('ip', '')
        if ip:
            try:
                result = subprocess.run(['ping', '-c', '1', '-W', '2', ip], 
                                       capture_output=True, timeout=3)
                status = '✓ UP' if result.returncode == 0 else '✗ DOWN'
            except:
                status = '✗ TIMEOUT'
            results.append((a['id'], ip, status))

    for aid, ip, status in sorted(results, key=lambda x: x[1]):
        print(f"  {aid:32s} {ip:16s} {status}")
    print()


def report_missing():
    """Lista assets con campos vacíos o incompletos."""
    print_separator()
    print("  CAMPOS FALTANTES EN ASSETS")
    print_separator()
    print()

    for a in registry_list('assets'):
        e = registry_get(a['id'])
        missing = []
        net = e.get('network', {})
        if not net.get('mac'):
            missing.append('MAC')
        if not net.get('hostname'):
            missing.append('hostname')
        if not e.get('manufacturer'):
            missing.append('manufacturer')
        if not e.get('location'):
            missing.append('location')
        
        if missing:
            print(f"  {a['id']:32s}: {', '.join(missing)}")
    
    print()


def report_fingerprint():
    """Sugiere comandos para fingerprinting DNS/SSH de cada host."""
    print_separator()
    print("  FINGERPRINTING — COMANDOS SUGERIDOS")
    print_separator()
    print()

    for a in registry_list('assets'):
        ip = a.get('network', {}).get('ip', '')
        if ip:
            print(f"  # {a['id']} ({ip})")
            print(f"  ping -c 1 {ip}")
            print(f"  ssh carlos@{ip} 'uname -n; cat /etc/os-release | grep PRETTY'")
            print(f"  # DNS fingerprint (si corre AdGuard):")
            print(f"  docker exec adguardhome tail -100 /opt/adguardhome/data/querylog.json | grep '\"IP\":\"{ip}\"'")
            print()


def main():
    if len(sys.argv) < 2:
        report_summary()
        return

    cmd = sys.argv[1]
    
    if cmd == '--host' and len(sys.argv) > 2:
        report_host(sys.argv[2])
    elif cmd == '--ports':
        report_ports()
    elif cmd == '--check':
        report_check()
    elif cmd == '--missing':
        report_missing()
    elif cmd == '--fingerprint':
        report_fingerprint()
    else:
        print(f"Uso: python3 {sys.argv[0]} [--host N|--ports|--check|--missing|--fingerprint]")
        sys.exit(1)


if __name__ == '__main__':
    main()