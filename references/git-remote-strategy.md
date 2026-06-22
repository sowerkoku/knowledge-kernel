# Git Remote Strategy for Registry

## El problema

Registry en Git local (`.52`) no protege contra:
- Incendio
- Robo
- Falla eléctrica general
- Cualquier evento que destruya el hardware

## Niveles de resiliencia

```
Nivel 1: Git local únicamente
→ Protege contra: errores de edición (historial, revert, diff)
→ NO protege contra: pérdida del equipo

Nivel 2: Git remoto en otro servidor de mi red (.54)
→ Protege contra: errores de edición
→ NO protege contra: desastre físico (si se quema la casa, se pierden ambos)

Nivel 3: Git remoto fuera de mi infraestructura (GitHub private)
→ Protege contra: todo lo anterior
→ Desventaja: dependes de un tercero (aceptable para documentación no sensible)
```

## Decisión tomada (2026-06-12)

**Opción C: GitHub private + clone local en .54**

```
.52 (Registry local)
    ↓ push
GitHub (private repo: github.com/sowerkoku/registry-cic)
    ↓ pull/clone
.54 (copia local operativa — futuro)
```

### Por qué GitHub solo no alcanza:
- Sin clone en .54, si GitHub cae o perdés acceso, quedás sin Registry
- Con clone en .54: operación sin internet + backup externo

### Por qué no basta con .54 solo:
- .54 está en la misma casa que .52
- Un desastre físico destruye ambos

## Implementación

```bash
# Generar SSH key (si no existe)
ssh-keygen -t ed25519

# Agregar clave pública en GitHub → Settings → SSH and GPG keys

# Verificar acceso
ssh -T git@github.com

# Agregar remote y push
cd /home/carlos/registry
git remote add origin git@github.com:sowerkoku/registry-cic.git
git branch -M main
git push -u origin main
```

## Estado actual (2026-06-12)

- Git local: ✅ `/home/carlos/registry/.git` (4 commits)
- Remote GitHub: ✅ `github.com/sowerkoku/registry-cic`
- Clone en .54: ⏳ Pendiente (futuro)
- Dominio propio (77d.cl): Disponible para Gitea self-hosted si se quiere más control

## Nota

El Registry contiene información operativa del CIC (IPs, nombres de servicios, relaciones, criticidad). No contiene credenciales ni secretos. Un repo privado en GitHub es apropiado para este nivel de sensibilidad.