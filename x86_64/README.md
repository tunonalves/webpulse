# web-load-test 1.4 multiportal - x86_64

Paquete reconstruido a partir del estado documentado del proyecto el 2026-08-18. No es una copia byte-a-byte del directorio original.

## Estado representado
- Python + Playwright 1.61.0 + Chromium + Docker Compose.
- Un contenedor/Chromium por portal.
- BrowserContext independientes por usuario.
- `headless: true`.
- JSONL por usuario, reinicio automático de sesiones y limpieza por antiguedad.
- Imagen objetivo: `web-load-test-playwright:1.4`.
- Cadena Rio conserva `/Noticias` y `section_content_wait_seconds: 2.5`.

## Uso
```bash
cp .env.example .env
./manage.sh up
./manage.sh ps
./manage.sh logs 200
./manage.sh stats
```

Los YAML de los cuatro portales no-Cadena usan `/` como sección de descubrimiento porque el material fuente no incluía sus rutas originales exactas.
