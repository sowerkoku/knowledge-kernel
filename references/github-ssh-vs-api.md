# GitHub: SSH vs API Token

## Dos sistemas distintos

GitHub tiene dos mecanismos de acceso ortogonalmente diferentes:

| Mecanismo | Usa para | Puede crear repo? | Puede hacer push? |
|---|---|---|---|
| SSH key | `git@github.com:user/repo.git` | ❌ No | ✅ Solo si repo existe |
| OAuth/PAT | REST API (`POST /user/repos`) | ✅ Sí | ✅ Sí (con token) |

## SSH Key
```
git remote add origin git@github.com:sowerkoku/repo.git
git push -u origin master
```
Funciona para **cualquier repo que ya exista**. Fallo si el repo no existe:
```
ERROR: Repository not found.
fatal: Could not read from remote repository.
```

GitHub no auto-crea repos al hacer push — eso sería un agujero de seguridad.

## OAuth/PAT (Personal Access Token)
```
curl -X POST https://api.github.com/user/repos \
  -H "Authorization: token $GITHUB_TOKEN" \
  -d '{"name":"nuevo-repo"}'
```
Necesario para:
- Crear repos
- Crear issues
- Gestionar permissions
- Cualquier operación que no sea clone/push

## En la práctica (Cico)

1. Crear repo manualmente en github.com, o usar PAT para crear por API
2. Agregar remote con SSH URL: `git remote add origin git@github.com:user/repo.git`
3. Push: `git push -u origin master`

SSH no puede crear, pero puede operar una vez que el repo existe.

## Verificar acceso SSH a GitHub
```bash
ssh -T git@github.com
# Expected: "Hi sowerkoku! You've successfully authenticated..."
```