#!/usr/bin/env python3
"""
Verify registry network ports against reality.

Usage:
    python3 verify_ports.py [--host HOST]

Runs on the machine where Docker containers are hosted (default: localhost).
For remote verification, use: ssh user@HOST 'python3 verify_ports.py'

Output:
    - Discrepancias entre Registry y realidad (docker inspect, ss, ps)
    - Parches sugeridos para YAMLs
"""

import sys
import subprocess
import json

sys.path.insert(0, '/home/carlos/.hermes/skills/registry')
from registry import registry_list, registry_get


def get_docker_ports():
    """Get actual port bindings from Docker containers."""
    r = subprocess.run(
        ['docker', 'ps', '--format', '{{.Names}}'],
        capture_output=True, text=True
    )
    containers = r.stdout.strip().split('\n')
    
    ports = {}
    for c in containers:
        if not c:
            continue
        # Get port bindings
        r2 = subprocess.run(
            ['docker', 'inspect', c, '--format', '{{json .HostConfig.PortBindings}}'],
            capture_output=True, text=True
        )
        try:
            bindings = json.loads(r2.stdout.strip())
            if bindings:
                for container_port, hosts in bindings.items():
                    if hosts:
                        host_port = hosts[0].get('HostPort', '')
                        ports[c] = {'container_port': container_port, 'host_port': host_port}
        except json.JSONDecodeError:
            continue
    
    return ports


def get_host_processes():
    """Get processes listening on ports (for network=host containers)."""
    r = subprocess.run(
        ['ss', '-tlnp'],
        capture_output=True, text=True
    )
    ports = {}
    for line in r.stdout.split('\n')[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 4:
            addr = parts[3]  # e.g., "0.0.0.0:8083"
            if ':' in addr:
                port = addr.split(':')[-1]
                ports[port] = line.strip()
    return ports


def verify_registry():
    """Compare Registry against reality."""
    docker_ports = get_docker_ports()
    host_procs = get_host_processes()
    
    print("=== REGISTRY vs REALIDAD: Verificación de Puertos ===\n")
    print(f"{'Servicio':22s} | {'Registry':15s} | {'Realidad':15s} | {'Status'}")
    print("-" * 75)
    
    updates_needed = []
    
    for s in registry_list('software'):
        e = registry_get(s['id'])
        net = e.get('network', {})
        host = net.get('host', '—')
        port = net.get('port', '—')
        rid = e['id']
        
        # Skip if no network info
        if host == '—' and port == '—':
            continue
        
        # Only check localhost services
        if host not in ['localhost', '127.0.0.1']:
            continue
        
        # Try to find in docker ports
        real_port = None
        for cname, cinfo in docker_ports.items():
            if rid.replace('-', '') in cname.replace('-', '') or \
               cname.replace('-', '') in rid.replace('-', ''):
                real_port = cinfo['host_port']
                break
        
        # If not in docker, check host processes
        if not real_port and str(port) in host_procs:
            real_port = str(port)  # Port matches, assume correct
        
        # Check for known patterns
        if not real_port:
            # Check if container exists but with different port
            for cname, cinfo in docker_ports.items():
                if rid in cname or cname in rid:
                    real_port = cinfo['host_port']
                    break
        
        if real_port and str(real_port) != str(port):
            status = "❌ PATCH"
            updates_needed.append((rid, str(port), str(real_port)))
        else:
            status = "✅ OK" if real_port else "— "
        
        real_display = f"localhost:{real_port}" if real_port else "no detectado"
        print(f"{rid:22s} | {str(host):10s}:{str(port):4s} | {real_display:14s} | {status}")
    
    print()
    print(f"Discrepancias encontradas: {len(updates_needed)}")
    for rid, reg_port, real_port in updates_needed:
        print(f"  {rid}: port {reg_port} → {real_port}")
        print(f"    File: /home/carlos/registry/software/{rid}.yaml")
        print(f"    Patch: 'port: {reg_port}' → 'port: {real_port}'")
    
    return updates_needed


if __name__ == '__main__':
    import os
    if os.geteuid() != 0:
        print("Nota: Algunos contenedores pueden requerir sudo para docker inspect")
    
    discrepancies = verify_registry()
    sys.exit(1 if discrepancies else 0)