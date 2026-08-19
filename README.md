# web-load-test 1.5 headful - x86_64

Paquete reconstruido a partir del estado documentado del proyecto el 2026-08-18. No es una copia byte-a-byte del directorio original.

## Estado representado
- VM Debian sobre Proxmox, x86_64.
- 5 contenedores / 5 Chromium headful ejecutados con Xvfb.
- 12 BrowserContext concurrentes: La Tecla 4, resto 2 por portal.
- Variables `BROWSER_HEADLESS` y `BROWSER_SLOW_MO_MS` con prioridad sobre YAML.
- `reading: 2.5-5 s`, `session restart: 30-60 s`.
- La Tecla usa stagger de 15 s; resto 8 s.
- Límites de referencia: CPU 1.25, RAM 1200m, shm 256m; La Tecla preparada para 1500m.
- Cadena Rio conserva `/Noticias` y `section_content_wait_seconds: 2.5`.

## Uso
```bash
cp .env.example .env
./manage.sh up
./manage.sh ps
./manage.sh follow
./manage.sh stats
./manage.sh inspect
```

Los YAML de los cuatro portales no-Cadena usan `/` como sección de descubrimiento porque el material fuente no incluía sus rutas originales exactas.
