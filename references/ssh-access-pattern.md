# SSH Access Pattern — CIC Infrastructure

## Contexto

Para operar el CIC, el agente necesita acceso SSH a los servidores principales. Este documento describe el patrón validado.

## Llave SSH actual

- **Tipo:** ed25519
- **Fingerprint:** `SHA256:XMDpmRbKWamTijUXFfo4ps8QjdvFoQHAzmJuFgdYix0`
- **Ubicación:** `/home/carlos/.ssh/id_ed25519` (en .52)
- **Fecha de generación:** 2026-06-12

## Equipos con acceso configurado

| Equipo | IP | Hostname | Estado |
|---|---|---|---|
| orange-pi-54 | 192.168.1.54 | orangepi3b | ✅ Working |
| server-192-168-1-53 | 192.168.1.53 | orangepizero3 | ✅ Working |

## Equipos Windows (no SSH)

| Equipo | IP | Rol | Acceso |
|---|---|---|---|
| servidor-pos | 192.168.1.2 | Caja POS Eleventa | ❌ Windows, no requiere SSH para CIC |
| caja-cliente | 192.168.1.4 | Terminal POS | ❌ Windows, no gestionado |

## Verificación de acceso

```bash
# Verificar que la key funciona
ssh -o ConnectTimeout=5 carlos@192.168.1.54 "hostname"
# Expected: orangepi3b

ssh -o ConnectTimeout=5 carlos@192.168.1.53 "hostname"
# Expected: orangepizero3
```

## Agregar la key a un nuevo equipo

```bash
# 1. Mostrar la clave pública
cat ~/.ssh/id_ed25519.pub

# 2. En el equipo destino, agregar a authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDRD/U49ckUWkMVWoVMPz9m3K3iIPs3mpW463hyZNL2U carlos" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Registry integration

El campo `network` en cada asset documenta:

```yaml
network:
  hostname: orangepi3b
  ip: 192.168.1.54
  ssh_port: 22
  ssh_user: carlos
  ssh_key_fingerprint: SHA256:XMDpmRbKWamTijUXFfo4ps8QjdvFoQHAzmJuFgdYix0
  ssh_access: verified_2026-06-12
```

## Git remote + SSH

El Registry está backuppeado en GitHub:

- **Remote:** `git@github.com:sowerkoku/registry-cic.git`
- **Branch:** main
- **Último push:** 2026-06-12

La misma clave SSH permite:
1. Acceder a los servidores del CIC
2. Pushear a GitHub (vía SSH)

## Disaster recovery

Si este equipo (.52) falla:

1. Clonar Registry desde GitHub en cualquier otro equipo:
   ```bash
   git clone git@github.com:sowerkoku/registry-cic.git
   ```

2. Copiar la clave SSH desde backup:
   ```bash
   cp /backup/.ssh/id_ed25519* ~/.ssh/
   chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_ed25519
   ```

3. Verificar acceso:
   ```bash
   ssh carlos@192.168.1.54 "hostname"
   ```

## Referencias

- GOVERNANCE.md → Sección "Acceso SSH"
- registry/assets/orange-pi-54.yaml
- registry/assets/server-192-168-1-53.yaml