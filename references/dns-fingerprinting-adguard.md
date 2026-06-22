# DNS Fingerprinting via AdGuard Home — Full Reference

> Método validado 2026-06-20: identificar dispositivos en la red analizando sus consultas DNS.
> Fuente: `querylog.json` de AdGuard Home corriendo en `.54` (docker, network=host, puerto 8083).

---

## Acceso al querylog

```bash
# 1. Conectar al host que corre AdGuard Home
ssh carlos@192.168.1.54

# 2. Config de AdGuard (autoritativo para puertos y paths)
docker exec adguardhome cat /opt/adguardhome/AdGuardHome.yaml

# 3. Logs DNS — están DENTRO del contenedor, no en el host
docker exec adguardhome tail -200 /opt/adguardhome/data/querylog.json

# 4. Filtrar por IP específica
docker exec adguardhome tail -500 /opt/adguardhome/data/querylog.json \
  | python3 -c "
import json, sys
ip_filter = '192.168.1.140'
domains = {}
for line in sys.stdin:
    try:
        e = json.loads(line.strip())
        if e.get('IP') == ip_filter:
            qh = e.get('QH','')
            if qh: domains[qh] = domains.get(qh, 0) + 1
    except: pass
for d, c in sorted(domains.items(), key=lambda x: -x[1]):
    print(f'{c:4d}  {d}')
"

# 5. Extraer todas las IPs únicas y sus dominios
docker exec adguardhome tail -1000 /opt/adguardhome/data/querylog.json \
  | python3 -c "
import json, sys
from collections import defaultdict
d = defaultdict(set)
for line in sys.stdin:
    try:
        e = json.loads(line.strip())
        ip = e.get('IP','')
        qh = e.get('QH','')
        if ip and qh:
            d[ip].add(qh)
    except: pass
for ip, doms in sorted(d.items()):
    print(f'{ip}:')
    for x in sorted(list(doms)[:10]):
        print(f'  {x}')
"
```

**Key path discovery (2026-06-20):** La binary de AdGuard está en `/opt/adguardhome/AdGuardHome` DENTRO del contenedor. El `querylog.json` está en `/opt/adguardhome/data/querylog.json` (dentro del contenedor, NO accesible directamente desde el host porque network=host). Siintentás `docker cp` o acceso desde el host, no existe ahí.

---

## Patrones de fingerprinting validados

| Dominio característico | Fabricante/dispositivo | Confianza |
|---|---|---|
| `authbe.sec.intl.miui.com` + `sdkconfig.ad.intl.xiaomi.com` | 📱 Xiaomi Android (MIUI) | alta |
| `api.miwifi.com` | 🏠 Xiaomi AP/router (Mi WiFi) | alta |
| `sdk.pushmessage.samsung.com` | 📱 Samsung Android | alta |
| `api16-access-wf-sg.pangle.io` + `a.gdflpr.com` | 📱 Android con TikTok/ByteDance | alta |
| `rr*r---sn-uxgg5-njae*.googlevideo.com` | 📺 Smart TV / Android TV (YouTube CDN) | alta |
| `play.googleapis.com` + `android.googleapis.com` (sin MIUI/Samsung) | 📱 Android genérico | media |
| `settings-win.data.microsoft.com` | 💻 Windows | media |
| `mobile.events.data.microsoft.com` | 💻 Windows (telemetry) | media |
| `edgedl.me.gvt1.com` | 📱 Android (Google Play updates) | media |
| `census-app.scorecardresearch.com` | 📱 App de analytics (no específico) | baja |

### Ejemplo: Xiaomi vs Samsung vs ByteDance

```
# Xiaomi (MIUI): authbe.sec.intl.miui.com, sdkconfig.ad.intl.xiaomi.com
#   → También consultas normales a Google (play.googleapis.com)
#   → Pattern: MIUI domains + Google services

# Samsung: sdk.pushmessage.samsung.com
#   → push notifications de Samsung Cloud
#   → Pattern: samsung.com domain + Google services

# ByteDance/TikTok: api16-access-wf-sg.pangle.io
#   → Pangle SDK de ByteDance para ads en apps
#   → Pattern: pangle.io + YouTube + census apps

# Smart TV: rr*r---sn-uxgg5-njae*.googlevideo.com
#   → YouTube video CDN — traffic intensivo
#   → Pattern: googlevideo.com CDN + i.ytimg.com
```

---

## Limitaciones del método

1. **Dispositivos inactivos** — Si no consultaron DNS en el período del log, no aparecen. El log rota cada 30 días (por defecto).
2. **DNS externo** — Si un dispositivo usa 8.8.8.8 o 1.1.1.1 en vez de AdGuard, no aparece. **Solo detecta lo que pasa por AdGuard.**
3. **Hosts sin tráfico DNS** — `.94` (PC principal de Carlos) no apareció en los últimos 500 logs. Puede estar activo con DNS cacheado o usando DNS externo.
4. **Smartphones en modo ahorro** — Pueden tener patrones DNS distintos (menos frecuentes).

---

## Workflow completo

```
PASO 1: ¿Qué hosts hay activos en la red?
  → ip neigh show (ARP table — fuente de verdad de IPs + MACs vivos)
  → git -C registry diff (últimos assets agregados vs realidad)

PASO 2: ¿Qué son los hosts desconocidos?
  → DNS fingerprinting: querylog por IP → dominios → patrón → tipo dispositivo
  → Si no hay logs DNS, marcar "pending-identify" (NO asumir)

PASO 3: ¿Qué servicios corren en cada host?
  → network_report.py --host <id>
  → docker ps (si es servidor con containers)
  → ss -tlnp (puertos escuchando)

PASO 4: Crear/actualizar asset con dns_fingerprint_YYYY-MM-DD
```

---

## Template de asset con DNS fingerprint

```yaml
network:
  hostname: xiaomi-140
  ip: 192.168.1.140
  mac: "90:fb:5d:6b:b6:c5"  # OUI: Xiaomi Mobile Software

dns_fingerprint_2026-06-20:
  method: "AdGuard Home querylog.json — docker exec adguardhome tail -200"
  sample_size: ~200 entradas
  key_domains:
    - authbe.sec.intl.miui.com       # MIUI auth (Xiaomi)
    - sdkconfig.ad.intl.xiaomi.com   # Xiaomi ad config
    - play.googleapis.com            # Google Play services
  notes: "Xiaomi Android activo — patrón MIUI + Google services confirmado"
```

---

## MAC OUI como complemento

El fingerprint DNS es más preciso que el OUI de MAC porque:
- **OUI** dice "fabricante" (Xiaomi = laptop + phone + router + tablet + IoT)
- **DNS** dice "tipo de dispositivo" (Xiaomi con MIUI domains = teléfono MIUI)

Usar ambos juntos:

```
MAC OUI:   90:fb:5d:6b:b6:c5 → Xiaomi Mobile Software
DNS pattern: authbe.sec.intl.miui.com → Teléfono Xiaomi (NO router, NO laptop)
Conclusión: Xiaomi Android phone
```

Para hacer lookup de OUI:
```bash
curl -s --max-time 3 "https://api.macvendors.com/AA:BB:CC:DD:EE:FF"
```
(Tiene rate limit — usar con cautela, 1 query por segundo máximo)

---

*Validado: 2026-06-20 con 7 dispositivos identificados*
*Limitación: requiere que AdGuard Home esté corriendo y tenga querylog habilitado*