# Error Log — Registry Skill

Fuente única de errores comunes detectados. Consolidado de 3 versiones previas en una sola lista.

---

## Errores Comunes — 30 errores

### Ownership y Asunciones

1. **Asumir localhost sin consultar Registry** → Primero ping/scan del host real. Registry tiene `runs_on: [asset_id]` que indica la máquina, no localhost.

2. **Usar skill Registry ANTES de asumir** → El agente debe consultar Registry antes de asumir IPs, ubicaciones, servicios. Ejemplo: "No usaste la skill registry" = error del agente.

3. **Asumir que NAS existe cuando es POS** → Verificar tipo de cada asset. En este proyecto: .2 = servidor-pos (Windows), NO es NAS.

4. **Asumir puertos de memoria** → Portainer decía 9000, realidad 9443. phpMyAdmin decía 8080, realidad 80. Lesson: ports cambian (Docker reconfig, HTTPS migration). Validar con `curl -I http://host:port` antes de confiar.

5. **numeric host matching (54 ≠ orange-pi-54 automáticamente)** → `--host 54` requiere fuzzy matching, no string comparison.

6. **Pre-push audit skipping** → риsko de datos no verificados. Cada cambio a registry/ debe validarse antes del commit.

### Relaciones y Grafos

7. **Mezclar runs_on con depends_on** → runs_on=host físico (1-hop lookup), depends_on=runtime/logical (BFS transitivo). Son consultas DISTINTAS.

8. **Contenedores con docker en runs_on** → Container corre EN orange-pi-54, DEPENDE DE docker para ejecutarse. Docker va en `depends_on`, no en `runs_on`.

9. **DBs con runs_on: [mysql]** → DB existe DENTRO de MySQL, no "corre en" MySQL como host. Corregido: `runs_on: [orange-pi-54]` + `depends_on: [mysql]`.

10. **Firebird como runs_on de firebird-eleventa** → Firebird es software, no host. Corregido: `runs_on: [servidor-pos]`.

11. **Mezclar impact funcional con co-ubicación** → Functional e infrastructure son consultas DISTINTAS. En audit de impacto, reportarlas SEPARADO, nunca sumarlas en "total afectados".

12. **Conflar categorías de recuperación** — reinstalable ≠ restaurable ≠ fuente de verdad ≠ fundacional. Usar clasificación R/RT/RC/RP antes de priorizar runbooks.

### Backup y Recuperabilidad

13. **Claim "backup.enabled=false" sin verificar realidad** → El usuario puede tener backups manuales fuera del modelo. El Registry subestimaba la capacidad real. Verificar con el usuario, no con el YAML.

14. **Concluir "es irrecuperable"** → Lo correcto es "recuperabilidad no demostrada" hasta verificar evidencia con el dueño.

15. **"backup existe" ≠ "restore funciona"** → Backup documentado no significa que se haya probado restaurar. Restore probado requiere evidencia operacional.

### YAML y Archivos

16. **Colones en campos YAML `name:`** → `name: Hermes (profile: arquitectobi)` causa `YAMLError: mapping values are not allowed`. Solución: usar comillas o evitar dos puntos internos.

17. **Patch tool con old_string idéntico** → Cuando el old_string a buscar aparece múltiples veces y solo una debe cambiarse, hay que incluir contexto único. Usar `write_file` si no hay contexto suficiente.

18. **IDs duplicados entre categorías bloquean el indexer** → Si `metabase` existe en `software/` Y en `endpoints/` con el mismo `id:`, el `_by_id[eid]` sobrescribe la primera entrada. Fix: sufijos diferenciadores (`metabase-ui.yaml`).

19. **Categoría nueva no reconocida hasta actualizar REGISTRY_CATEGORIES** → El indexer tiene `REGISTRY_CATEGORIES` hardcodeado. Sin agregarlo, `registry_validate()` muestra stats incorrectas. Fix: editar `indexer.py` línea ~20.

20. **Endpoints sin campo `name`** → `registry_list('endpoints')` hace `_by_id[eid]["name"]` y lanza KeyError. El campo `name` es requerido por el indexer. Mínimo 3 caracteres.

### Red y Servicios

21. **Curl localhost para validar docker port-mapping** → Containers con `--network=host` no tienen port bindings visibles en `docker ps`. Usar `ss -tlnp` en el host + curl.

22. **No detectar containers en network=host** → Containers con `--network=host` no aparecen en `docker ps --format "{{.Ports}}"`. Puertos: 3000 (metabase), 8080 (open-webui), 80 (phpmyadmin), 8083 (adguardhome), 53 (unbound). Verificar con `ss -tlnp`.

23. **AdGuard Home paths requieren docker exec** → El querylog está dentro del container, no en el host. `docker exec adguardhome cat /opt/adguardhome/data/querylog.json`.

24. **`network.host: localhost` en servicios remotos** → Regla: `network.host` = IP del asset en `runs_on`, nunca localhost salvo que el servicio corra en la máquina donde se ejecutan las queries.

### DNS y Fingerprinting

25. **Fingerprint de DNS no confirmado = no asumir tipo de dispositivo** → RevenueCat apareció como "iPhone" pero .128 era Samsung Galaxy A71. Xiaomi MiWiFi apareció como "laptop" pero .101 era router. Solo la evidencia del usuario o acceso físico confirma.

26. **DNS fingerprinting: MiWiFi + NTP pool + baidu = router, no laptop** → Si fuera laptop, tendría browser queries (chrome, login.live.com). La ausencia de browser activity indica device sin GUI.

27. **No todo en loopback 127.0.0.x es el mismo servidor** → .54 tiene Unbound en `127.0.0.54:53` (network=host container). .53 tiene systemd-resolved en `127.0.0.53:53`. Son servicios distintos.

28. **Puerto 5335 en .54 es localhost-only** → Escucha en `127.0.0.1:5335`, no expuesto externamente. No aparece en docker ps. Identificar via `ss -tlnp` vía SSH directo al host.

### Git y Gobernanza

29. **Git initialized ≠ gobernanza cerrada** → Git resuelve historial/reversión/diff. No resuelve: remote push, backup externo, proceso disciplinado.

30. **Assets pending-identify → usar `status: pending-identify`** → MAC placeholder `52:54:00:...` indica QEMU/VM, no hardware real. Verificar con `arp -an` y SSH directo.