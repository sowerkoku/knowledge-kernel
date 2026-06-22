# DNS Fingerprinting — Domain → Device Type Patterns

**Source:** AdGuard Home querylog on 192.168.1.54  
**Date:** 2026-06-21 (actualizado sesión de auditoría)  
**Scope:** Patterns derived from real querylog entries cross-referenced with known devices.

---

## Confirmed Patterns — VALIDADO 2026-06-21

### Windows PC (desktop/laptop)
```
_5222._https.web.whatsapp.com     # WhatsApp Desktop
chrome.cloudflare-dns.com         # Chrome browser
ctldl.windowsupdate.com           # Windows Update
edgedl.me.gvt1.com                # Edge browser update
login.live.com                    # Microsoft account login
mobile.events.data.microsoft.com   # Windows telemetry
settings-win.data.microsoft.com   # Windows settings sync
officeclient.microsoft.com         # Microsoft Office
updates.bravesoftware.com         # Brave browser update
```
**IP confirmado:** 192.168.1.4

### Smartphone Android — Samsung Galaxy A71 ← VALIDADO 2026-06-21
```
api.revenuecat.com                # RevenueCat (iOS subscriptions — también se usa en Android)
api.whatsapp.net                  # WhatsApp
b-graph.facebook.com              # Facebook Graph API
b-graph-fallback.facebook.com     # Facebook fallback
app-measurement.com               # Firebase/Google Analytics
clients4.google.com               # Google services
```
**IP confirmado:** 192.168.1.128  
**Nota:** La presencia de RevenueCat NO implica iOS — Samsung Galaxy A71 también lo usa.

### Smartphone Android — TikTok user
```
analytics.us.tiktok.com           # TikTok analytics
analytics-tcp.mtgglobals.com      # TikTok ad tracking
a.gdflpr.com                      # TikTok CDN
a.gdfsnt.com                      # TikTok CDN
android.clients.google.com        # Google Play Services
2.android.pool.ntp.org            # Android NTP sync
```
**IP confirmado:** 192.168.1.144

### AP/Router Xiaomi ← VALIDADO 2026-06-21 (NO es laptop)
```
api.miwifi.com                    # MiWiFi (firmware del router Xiaomi)
www.baidu.com                     # Servicios chinos
0.cn.pool.ntp.org                 # NTP pool China
0.pool.ntp.org                    # NTP pool
1.pool.ntp.org                    # NTP pool
2.pool.ntp.org                    # NTP pool
3.pool.ntp.org                    # NTP pool
```
**IP confirmado:** 192.168.1.101  
**Lección:** MiWiFi + NTP pool + baidu juntos = router Xiaomi, NO laptop. Un device que es solo router no hace queries desde browsers.

### Smartphone Android — Xiaomi
```
api.ad.intl.xiaomi.com            # Xiaomi Ad ID API
spot-pa.googleapis.com            # Google API
time.android.com                  # Android time sync
```
**IP confirmado:** 192.168.1.140

### Smart TV / YouTube device
```
discover-pa.googleapis.com         # Google Cast / YouTube discovery
encrypted-tbn0.gstatic.com        # YouTube thumbnail
encrypted-tbn1.gstatic.com        # YouTube thumbnail
encrypted-tbn2.gstatic.com        # YouTube thumbnail
encrypted-tbn3.gstatic.com        # YouTube thumbnail
```
**IP confirmado:** 192.168.1.148

### Linux server / Orange Pi con Telegram + Ollama
```
api.telegram.org                  # Telegram bot API
models.dev                        # LLM model registry
www.schemastore.org               # JSON schema catalog
ollama.com                        # Ollama LLM inference server
```
**IP confirmado:** 192.168.1.52  
**Nota:** .52 no tiene Docker corriendo, pero tiene SSH y procesos de red. Queries desde el propio servidor.

### POS / Servidor Windows
```
mobile.events.data.microsoft.com   # Windows telemetry
settings-win.data.microsoft.com   # Windows settings
updates.bravesoftware.com          # Browser updates
```
**IP confirmado:** 192.168.1.2 (servidor-pos)

---

## Método COMPLETO de auditoría

```bash
# Paso 1: Ping sweep de toda la red
for ip in 192.168.1.{1,2,4,52,53,54,60,77,100,101,103,105,110,112,116,120,122,128,133,136,140,144,148}; do
  timeout 2 ping -c 1 -W 1 $ip 2>/dev/null | grep -q "1 received" && echo "$ip UP" || echo "$ip DOWN"
done

# Paso 2: Port scan de hosts clave
for ip in 192.168.1.1 192.168.1.54; do
  echo -n "$ip: "
  for port in 22 80 443 3000 3306 5000 8080 8888 9000 9443; do
    timeout 1 bash -c "echo >/dev/tcp/$ip/$port" 2>/dev/null && echo -n "$port " || true
  done
  echo
done

# Paso 3: Servicios en .54 (network=host containers no aparecen en docker ps)
ssh carlos@192.168.1.54 'ss -tlnp'
ssh carlos@192.168.1.54 'docker ps --format "{{.Names}}:{{.Ports}}"'

# Paso 4: Identificar containers network=host (no tienen port bindings)
ssh carlos@192.168.1.54 'docker ps --filter "network=host" --format "{{.Names}}"'

# Paso 5: DNS fingerprinting vía AdGuard
ssh carlos@192.168.1.54 'docker exec adguardhome tail -1000 /opt/adguardhome/data/querylog.json' 2>/dev/null | python3 -c "
import json,sys
from collections import defaultdict
domains_by_ip = defaultdict(set)
for line in sys.stdin:
    try:
        entry = json.loads(line.strip())
        ip = entry.get('IP','')
        qh = entry.get('QH','')
        if ip and qh: domains_by_ip[ip].add(qh)
    except: pass
for ip,doms in sorted(domains_by_ip.items()):
    print(f'{ip}: {len(doms)} domains')
    for d in sorted(list(doms))[:8]: print(f'  - {d}')
"

# Paso 6: Identificar servicios desconocidos en puertos
ssh carlos@192.168.1.54 'curl -sI --max-time 2 http://localhost:3000/ | head -1'
ssh carlos@192.168.1.54 'curl -sI --max-time 2 http://localhost:8080/ | head -1'
```

**SECUENCIA OBLIGATORIA:** ping sweep → port scan → ss -tlnp → docker ps (incluye network=host) → adguard querylog → curl de identificación

---

## Limitaciones

- Devices con DNS externo hardcodeado (8.8.8.8, 1.1.1.1) **no aparecen** en querylog. Muestran UP en ping pero invisibles para fingerprinting.
- Un solo device puede mostrar múltiples OS fingerprints si corre múltiples apps/browsers.
- MAC addresses no disponibles desde AdGuard — usar ARP o tabla DHCP del router.
- Puerto 5335 en .54 es localhost-only (127.0.0.x), no expuesto externamente — servicio desconocido.

---

## Unknown devices (UP pero no en AdGuard querylog)

Estos IPs respondieron a ping pero no aparecen en DNS queries (DNS externo hardcodeado):

```
192.168.1.100   # desconocido
192.168.1.103   # desconocido
192.168.1.105   # desconocido
192.168.1.110   # desconocido
192.168.1.122   # desconocido
```

Para identificar: tabla DHCP del router (.1:80, credentials Support:Bk8nKiXs), o nmap OS detection.

---

## LECCIONES APRENDIDAS (2026-06-21)

1. **No asumir tipo de device por la presencia de un dominio.** RevenueCat (api.revenuecat.com) aparecía como "iPhone pattern" pero es Samsung Galaxy A71. Solo la confirmación del usuario o acceso físico al dispositivo lo descarta.
2. **MiWiFi + NTP pool = router Xiaomi, no laptop.** Si fuera laptop, tendría también browser queries (chrome.cloudflare-dns.com, login.live.com, etc.).
3. **SSH es el cuello de botella para identificación.** Los unknown devices no tienen SSH abierto — no se puede hacer `uname -a` ni `cat /sys/class/net/*/address`.
4. **ARP incomplete ≠ device inexistente.** .60 mostró `INCOMPLETE` en ARP pero aún existe en la red (respuesta ICMP), solo que la MAC no está en cache. Puede estar dormido o movido.
5. **Verificar antes de corregir el Registry.** El agente inferred "iPhone" y "laptop" basándose en patterns — el usuario tenía que corregir. Mejor: señalar como `type: pending-identify` hasta confirmar con evidencia adicional.