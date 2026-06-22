# Asset Audit Pattern — Registry vs Realidad (Red/Identidad Física)

> Anexo de `SKILL.md` **Nivel 8**. Detalle operativo: comandos exactos, pitfalls reales, tabla de discrepancias de la auditoría 2026-06-20.

## Por qué existe este patrón

Los YAML en `registry/assets/` pueden contener **datos sin verificar** que persisten meses porque:

1. **No hay un `registry_validate()`** que cruce campos de assets contra la red real.
2. **MAC placeholders** (típicos `52:54:00:12:34:56` de QEMU/libvirt, `02:42:...` de Docker bridge) se cuelan al copiar/pegar de plantillas.
3. **`status: operational`** es el default y rara vez se actualiza cuando un host queda apagado.
4. **`hostname: Desconocido`** se queda así indefinidamente porque nadie corrió `uname -n`.

Resultado: el Registry termina diciendo "todo OK" sobre hosts que hace meses no encienden. Eso rompe decisiones operativas (ej: "¿puedo migrar datos desde .54?" — la respuesta debería basarse en `ip neigh`, no en el YAML).

## Comando mínimo viable

Correr desde el equipo donde está el agent (asume Linux):

```bash
# 1. Lo que dice el Registry
cd ~/.hermes/skills/registry && python3 -c "
from registry import registry_list, registry_get
for a in registry_list('assets'):
    e = registry_get(a['id'])
    n = e.get('network', {})
    print(f\"{a['id']:25} ip={n.get('ip','—'):16} mac={n.get('mac','—'):20} status={e.get('status','—')}\")
"
```

```bash
# 2. Lo que dice la realidad de red
echo "=== PING ===" && for ip in 192.168.1.{2,52,53,54,60,77}; do
  timeout 2 ping -c 1 -W 1 $ip 2>/dev/null | grep -q "from" && echo "  $ip UP" || echo "  $ip DOWN"
done
echo "=== ARP ===" && ip neigh | grep -v FAILED
```

```bash
# 3. MAC e identidad de la máquina local (autoritativo sin SSH)
ip -4 addr show                                # IP propia
cat /sys/class/net/end0/address                # MAC propia (o eth0)
hostname && uname -n                           # Hostname OS
cat /etc/os-release | grep PRETTY              # Distro
cat /sys/firmware/devicetree/base/serial-number 2>/dev/null   # Serial SBC (Orange Pi)
```

```bash
# 4. MAC y hostname por host vivo (via SSH)
for ip in 192.168.1.52 192.168.1.54; do
  echo "--- $ip ---"
  ssh -o ConnectTimeout=5 carlos@$ip "
    echo -n 'MAC: '; cat /sys/class/net/*/address | head -1
    echo -n 'Hostname: '; uname -n
    echo -n 'Serial: '; cat /sys/firmware/devicetree/base/serial-number 2>/dev/null || echo 'N/A'
    echo -n 'Distro: '; cat /etc/os-release | grep PRETTY_NAME
  "
done
```

```bash
# 5. Hosts sin SSH (Windows POS): ping + ARP son la evidencia
ping -c 1 192.168.1.2
ip neigh show 192.168.1.2   # debe mostrar lladdr=...
```

## Tabla de discrepancias — auditoría 2026-06-20

Hallazgos aplicados en `git diff` del repo `home/carlos/registry`:

| Asset | Campo | Antes | Después | Fuente de verdad |
|-------|-------|-------|---------|------------------|
| orange-pi-54 | `network.mac` | `52:54:00:12:34:56` (placeholder QEMU) | `b2:34:3a:b5:fc:26` | `ip neigh` ARP + `/sys/class/net/*/address` |
| orange-pi-54 | `network.ssh_access` | `verified_2026-06-12` | `verified_2026-06-20` | día de la auditoría |
| server-192-168-1-52 | `network.mac` | (faltaba) | `40:95:cc:ed:a6:1b` | `/sys/class/net/*/address` via SSH |
| server-192-168-1-52 | `network.serial_number` | (faltaba) | `33802000eab8d2c6` | `/sys/firmware/devicetree/base/serial-number` |
| server-192-168-1-53 | `network.mac` | (faltaba) | `02:00:b2:1a:29:96` | `cat /sys/class/net/end0/address` local |
| server-192-168-1-53 | `network.hostname` | `orangepizero3` (rol confunde) | `orangepizero3  # OS hostname real; "hermes" es el rol` | aclarar role ≠ hostname |
| servidor-pos | `network.mac` | (faltaba) | `68:1d:ef:28:90:0d` | ARP `ip neigh` |
| servidor-pos | bloque nuevo | (no existía) | `verified_2026-06-20: {ping:true, ssh_22:refused, arp_resolved:true}` | evidencia de host vivo sin SSH |
| pc-oficina | `status` | `operational` | `unknown  # Ping ARP 2026-06-20: fallo (FAILED)` | ARP FAILED → no se puede afirmar operational |
| server-192-168-1-77 | bloque nuevo | (no existía) | `verified_2026-06-20: {ping:timeout, arp:FAILED, note:...}` | sigue powered-off, timestamp + nota |

## Senales RED FLAG en YAML asset

```bash
# Detección rápida de campos sospechosos
cd /home/carlos/registry/assets && grep -rE "^  mac: \"52:54|02:42:[a-f0-9]" *.yaml
cd /home/carlos/registry/assets && grep -L "verified_20" *.yaml   # assets sin fecha de verificación
```

| Red flag | Acción |
|----------|--------|
| `mac: "52:54:..."` | MAC QEMU default — reemplazar con MAC real de `ip neigh` |
| `mac: "02:42:..."` | MAC Docker bridge default — está bien si es contenedor, mal si es host físico |
| MAC ausente | Agregar la de `/sys/class/net/.../address` o `ip neigh` |
| `status: operational` sin bloque `verified_...` | Re-validar con ping/ARP, agregar fecha |
| `hostname: Desconocido` | Correr `uname -n` y actualizar |
| `ip: X.X.X.X` + ARP FAILED actual | Marcar `status: unknown` hasta confirmar |

## Pitfalls documentados (lecciones de la auditoría real)

1. **Multi-line SSH con comillas anidadas** — `ssh host 'cmd1\ncmd2'` falla con `unexpected EOF` porque bash interpreta el backslash antes de enviar. **Fix:** un comando por línea (`ssh host "cmd1"; ssh host "cmd2"`), o separar con `;` dentro de comillas simples bien balanceadas.

2. **SSH asimétrico entre hosts** — SSH de `.54 → .53` falla con `Permission denied` aunque SSH de `.53 → .54` funcione (la keychain es unidireccional por authorized_keys). **Fix:** para auditar `.53` mismo (donde corre Hermes), usa `cat /sys/class/...` local en vez de SSH entrante.

3. **`curl http://localhost:PORT` puede NO usar docker port-mapping desde el host** — Cuando un contenedor tiene `network_mode: host` y otro servicio está escuchando nativo en el mismo puerto, curl desde localhost puede responder con el servicio nativo (no mapeado). **Fix:** confiar en `docker inspect .HostConfig.PortBindings` (autoritativo) y `ss -tlnp` (procesos). curl es solo para verificar contenido, no para validar mapeos.

4. **MACs de eth0/end0 pueden tener NICs virtuales adicionales** — `cat /sys/class/net/*/address` puede mostrar muchas MACs (docker bridges, veth pairs). **Fix:** limitar a la primera NIC física (`ip route show default | awk '{print $5}' | head -1` para detectar la interfaz uplink).

## Hosts descubiertos pero NO documentados (gap candidates)

Durante la auditoría de 2026-06-20, `ip neigh` reveló hosts en la LAN que el Registry no conoce:

```
192.168.1.1   → router/gateway (08:33:ed:cd:7e:a0)
192.168.1.4   → device (a4:a4:d3:1a:cc:1f)   — ¿?
192.168.1.94  → device (00:26:c6:64:ee:5e)   — ¿?
192.168.1.122 → device (90:fb:5d:6b:b6:c5)   — ¿smartphone/IoT?
192.168.1.128 → device (80:20:fd:45:e0:04)   — ¿?
192.168.1.144 → device (72:14:ef:a2:c1:ee)   — ¿?
```

**Regla (Rule 0):** No se agregan al Registry **por anticipación**. Si una pregunta operativa las necesita (ej: "¿qué smartphones hay en la red?"), entonces se hace un barrido y se agregan. Mientras tanto, viven solo en este documento como candidatos.

## Automatización

`scripts/verify_assets.py` ejecuta los pasos 1–4 desde local y produce una tabla `Registry vs Realidad` con sugerencias de patch para los YAMLs. Útil para correr mensualmente o después de cualquier cambio físico en la red.
