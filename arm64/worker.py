#!/usr/bin/env python3
import asyncio
import json
import os
import random
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

STOP_EVENT = asyncio.Event()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name, default):
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def env_float(name, default):
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


def load_config():
    path = Path(os.getenv("PORTAL_CONFIG", "/app/config.yaml"))
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["_config_path"] = str(path)
    return cfg


def ensure_dirs(cfg):
    log_dir = Path(os.getenv("LOG_DIR", "/app/logs"))
    report_dir = Path(os.getenv("REPORT_DIR", "/app/reports"))
    log_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    return log_dir, report_dir


def cleanup_old_files(directory, max_age_days):
    if max_age_days <= 0:
        return
    cutoff = time.time() - max_age_days * 86400
    for item in directory.glob("*"):
        try:
            if item.is_file() and item.stat().st_mtime < cutoff:
                item.unlink()
        except OSError:
            pass


def append_jsonl(path, data):
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(data, ensure_ascii=False) + "\n")


def same_host(url, base_url):
    try:
        return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()
    except Exception:
        return False


def looks_like_article(url, cfg):
    parsed = urlparse(url)
    path = parsed.path or "/"
    if not same_host(url, cfg["base_url"]):
        return False
    if path in {"", "/"}:
        return False
    skip = cfg.get("discovery", {}).get("skip_path_contains", [])
    if any(token.lower() in path.lower() for token in skip):
        return False
    extensions = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf", ".mp4", ".mp3", ".zip")
    if path.lower().endswith(extensions):
        return False
    return True


async def discover_articles(page, section_url, cfg):
    nav = cfg.get("navigation", {})
    timeout_ms = int(nav.get("timeout_ms", 30000))
    await page.goto(section_url, wait_until="domcontentloaded", timeout=timeout_ms)
    wait_seconds = float(nav.get("section_content_wait_seconds", 0))
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    hrefs = await page.locator("a[href]").evaluate_all(
        "els => els.map(a => a.href).filter(Boolean)"
    )
    unique = []
    seen = set()
    for href in hrefs:
        absolute = urljoin(section_url, href).split("#", 1)[0]
        if absolute in seen:
            continue
        if looks_like_article(absolute, cfg):
            seen.add(absolute)
            unique.append(absolute)
    return unique


def choose_articles(items, fixed_count, random_count):
    fixed = items[:fixed_count]
    remaining = [x for x in items if x not in fixed]
    random_part = random.sample(remaining, min(random_count, len(remaining)))
    return fixed + random_part


async def simulate_reading(page, cfg):
    reading = cfg.get("reading", {})
    min_wait = float(reading.get("min_wait_seconds", 2.5))
    max_wait = float(reading.get("max_wait_seconds", 5.0))
    scroll_steps_min = int(reading.get("scroll_steps_min", 2))
    scroll_steps_max = int(reading.get("scroll_steps_max", 5))

    steps = random.randint(scroll_steps_min, max(scroll_steps_min, scroll_steps_max))
    total_wait = random.uniform(min_wait, max(max_wait, min_wait))
    per_step = total_wait / max(steps, 1)

    for _ in range(steps):
        await page.mouse.wheel(0, random.randint(350, 900))
        await asyncio.sleep(per_step)


async def install_route_blocking(context, cfg):
    blocked = set(cfg.get("browser", {}).get("block_resource_types", ["image", "media", "font"]))

    async def handler(route):
        if route.request.resource_type in blocked:
            await route.abort()
        else:
            await route.continue_()

    await context.route("**/*", handler)


async def run_one_session(browser, cfg, user_id, report_path):
    browser_cfg = cfg.get("browser", {})
    nav_cfg = cfg.get("navigation", {})
    selection = cfg.get("selection", {})

    context = await browser.new_context(
        viewport={"width": 1366, "height": 768},
        locale=browser_cfg.get("locale", "es-AR"),
        timezone_id=browser_cfg.get("timezone_id", "America/Argentina/Buenos_Aires"),
        user_agent=browser_cfg.get("user_agent") or None,
    )
    await install_route_blocking(context, cfg)
    page = await context.new_page()

    ok = 0
    errors = 0
    discovered_total = 0
    selected_urls = []

    try:
        all_articles = []
        seen = set()
        for section_name, section_path in cfg.get("sections", {"inicio": "/"}).items():
            section_url = urljoin(cfg["base_url"], section_path)
            try:
                articles = await discover_articles(page, section_url, cfg)
                print(f"[{user_id}] {section_name}: {len(articles)} noticias detectadas", flush=True)
                for url in articles:
                    if url not in seen:
                        seen.add(url)
                        all_articles.append(url)
            except Exception as exc:
                errors += 1
                print(f"[{user_id}] ERROR descubriendo {section_name}: {exc}", flush=True)

        discovered_total = len(all_articles)
        fixed_count = int(selection.get("fixed_count", 5))
        random_count = int(selection.get("random_count", 5))
        selected_urls = choose_articles(all_articles, fixed_count, random_count)
        print(f"[{user_id}] seleccionadas: {len(selected_urls)} ({fixed_count} fijas + hasta {random_count} aleatorias)", flush=True)

        for idx, url in enumerate(selected_urls, 1):
            if STOP_EVENT.is_set():
                break
            started = time.monotonic()
            result = {
                "ts": now_iso(),
                "portal": cfg.get("name"),
                "user": user_id,
                "url": url,
                "position": idx,
            }
            try:
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=int(nav_cfg.get("timeout_ms", 30000)),
                )
                await simulate_reading(page, cfg)
                result.update({
                    "ok": True,
                    "status": response.status if response else None,
                    "elapsed_seconds": round(time.monotonic() - started, 3),
                })
                ok += 1
            except PlaywrightTimeoutError as exc:
                result.update({"ok": False, "error": f"timeout: {exc}"})
                errors += 1
            except Exception as exc:
                result.update({"ok": False, "error": str(exc)})
                errors += 1
            append_jsonl(report_path, result)

    finally:
        await context.close()

    print(f"[{user_id}] FIN sesión: OK={ok}, ERROR={errors}", flush=True)
    return {"ok": ok, "errors": errors, "discovered": discovered_total}


async def user_loop(browser, cfg, user_number, report_dir):
    user_id = f"usuario_{user_number:02d}"
    stagger = float(cfg.get("navigation", {}).get("user_start_stagger_seconds", 0))
    initial_delay = stagger * (user_number - 1)
    if initial_delay > 0:
        print(f"[{user_id}] inicio escalonado: {initial_delay:.1f}s", flush=True)
        try:
            await asyncio.wait_for(STOP_EVENT.wait(), timeout=initial_delay)
            return
        except asyncio.TimeoutError:
            pass

    report_path = report_dir / f"{user_id}.jsonl"
    session_cfg = cfg.get("session", {})
    min_restart = float(session_cfg.get("min_restart_wait_seconds", 30))
    max_restart = float(session_cfg.get("max_restart_wait_seconds", 60))

    while not STOP_EVENT.is_set():
        try:
            await run_one_session(browser, cfg, user_id, report_path)
        except Exception as exc:
            print(f"[{user_id}] ERROR de sesión: {exc}", flush=True)

        wait_seconds = random.uniform(min_restart, max(max_restart, min_restart))
        print(f"[{user_id}] nueva sesión en {wait_seconds:.1f}s", flush=True)
        try:
            await asyncio.wait_for(STOP_EVENT.wait(), timeout=wait_seconds)
        except asyncio.TimeoutError:
            pass


async def main():
    cfg = load_config()
    log_dir, report_dir = ensure_dirs(cfg)
    cleanup_days = int(cfg.get("retention", {}).get("max_age_days", 7))
    cleanup_old_files(log_dir, cleanup_days)
    cleanup_old_files(report_dir, cleanup_days)

    yaml_headless = bool(cfg.get("browser", {}).get("headless", True))
    headless = env_bool("BROWSER_HEADLESS", yaml_headless)
    slow_mo = env_int("BROWSER_SLOW_MO_MS", int(cfg.get("browser", {}).get("slow_mo_ms", 0)))
    users = env_int("USERS", int(cfg.get("users", 1)))

    print(f"[SYSTEM] Portal: {cfg.get('name')}", flush=True)
    print(f"[SYSTEM] Config: {cfg.get('_config_path')}", flush=True)
    print(f"[SYSTEM] Usuarios: {users}", flush=True)
    print(f"[SYSTEM] Chromium headless: {headless}", flush=True)
    print(f"[SYSTEM] Chromium slow_mo: {slow_mo} ms", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=["--disable-dev-shm-usage"],
        )
        try:
            tasks = [asyncio.create_task(user_loop(browser, cfg, i, report_dir)) for i in range(1, users + 1)]
            await asyncio.gather(*tasks)
        finally:
            await browser.close()


def request_stop(*_):
    if not STOP_EVENT.is_set():
        STOP_EVENT.set()


if __name__ == "__main__":
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, request_stop)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
