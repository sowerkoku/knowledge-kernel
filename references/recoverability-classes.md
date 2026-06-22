# Recoverability Classes — R/RT/RC/RP

> 4 clases para clasificar **costo de recuperación**, NO solo tiempo de caída.
> Aprendido de `registry@.52` (Nivel 4.5) — tabla de referencia CIC incluida.

## Las 4 clases

| Clase | Significado | Tiempo típico | Método |
|-------|-------------|---------------|--------|
| **R**  | Se **rein**stala | < 30 min | apt install / docker-compose up |
| **RT** | Se **res**taura | 30-60 min | mysqldump → restore |
| **RC** | Se **rec**onstruye | horas-días | desde otro source/data + reconfiguración |
| **RP** | Se **r**eem**p**laza | semanas | adquisición de hardware |

## Diferencia clave vs RTO/RPO

| Métrica | Qué mide | Pregunta |
|---------|----------|----------|
| **RTO** | Tiempo tolerable de caída | "¿Cuánto puede estar caído?" |
| **RPO** | Datos tolerable a perder | "¿Cuántos datos puedo perder?" |
| **R/RT/RC/RP** | Esfuerzo/COMPLEJIDAD de recuperación | "¿Qué hay que hacer para recuperarlo?" |

**RTO/RPO mide continuidad. R/RT/RC/RP mide costo.**

## Tabla de referencia CIC (junio 2026, registry@.52)

| Entidad | Clase | Gap | Acción priorizada |
|---------|-------|-----|---------------------|
| firebird-eleventa | RC (reingreso manual) | CRÍTICO | Runbook de reingreso manual |
| servidor-pos | RP (hardware) | CRÍTICO | Backup de configuración + runbook alternativo |
| orange-pi-54 | RC (reconstrucción) | ALTO | Backup de Docker images + YAMLs en git |
| mysql | RT (mysqldump) | MEDIO | Probar restore verificable |
| mysql-db-raw | RT (sync restore) | BAJO | Runbook de restore |
| mysql-db-cic | RT (backup) | BAJO | Runbook de restore |
| docker | R (apt install) | NINGUNO | docker-compose up -d |
| metabase | R (docker-compose) | NINGUNO | trivial |
| portainer | R (docker-compose) | NINGUNO | trivial |
| adguardhome | R (docker-compose) | NINGUNO | trivial |
| unbound | R (docker-compose) | NINGUNO | trivial |
| searxng | R (docker-compose) | NINGUNO | trivial |
| open-webui | R (docker-compose) | NINGUNO | trivial |

## Cómo usar R/RT/RC/RP

1. **Una entidad = una clase principal**, pero puede tener componentes de varias.
2. **`R` no requiere runbook elaborado** — solo `docker-compose up -d` o `apt install`.
3. **`RT` requiere runbook de restore probado** — sin test runtime, no es RT real, es "RC con suposición".
4. **`RC` requiere documentación de fuentes de verdad** — ¿de dónde reconstruyo?
5. **`RP` requiere plan de adquisición** — nuevo hardware lleva semanas.

## Anti-patrones

❌ "Es R, lo reinstalo en 5 min" → ¿Y los datos? ¿Las configuraciones? R = fresh install, vacío.
❌ "Es RT, tengo backup" → ¿Probaste restaurar? `backup.enabled=true` ≠ restore funciona.
❌ "Es RC porque no tengo backup" → RC es **reconstrucción desde otro source**. Si no hay source, es RP (irrecuperable).

## Lección práctica

En `registry@.52` v1.6 el modelo decía `firebird-eleventa: backup.enabled: false` → algunos agentes concluyeron "irrecuperable". 

**Corrección de formulación:**
- ❌ NO decir "X es irrecuperable"
- ✅ DECIR "X es la única entidad crítica cuya recuperabilidad no está demostrada"

Diferencia: la segunda es verificable operacionalmente. La primera es una conclusión absoluta.

## Cuándo ascender una clase

Si el restore de un backup **nunca se probó**, la entidad baja de RT → RC hasta que se demuestre runtime. Es la regla "evidencia sobre modelo".
