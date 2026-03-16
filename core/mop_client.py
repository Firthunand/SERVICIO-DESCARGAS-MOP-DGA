from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
import os
import threading
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from core.naming import expected_filename_for, parse_year_from_period
from core.downloads import (
    downloads_folder_for_subfolder,
    find_existing_files_for_code,
    wait_for_new_xls_and_rename,
)
from core.pozos import (
    load_pozos_map,
    move_report_to_destination,
)

ROOT1 = "https://snia.mop.gob.cl/cExtracciones2/#/busquedaPublica"
CLICK_NAV_WAIT = 8


def wait_page_loaded(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def wait_overlay_gone(driver, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((By.ID, "waitingScreen"))
        )
    except Exception:
        pass


def click_mediciones(driver, timeout=15) -> bool:
    wait = WebDriverWait(driver, timeout)
    xpaths = [
        "//button[normalize-space()='Mediciones']",
        "//*[self::button or self::a][contains(normalize-space(.),'Mediciones')]",
        "//span[contains(normalize-space(.),'Mediciones')]/ancestor::button[1]",
    ]

    for xp in xpaths:
        try:
            wait_overlay_gone(driver, timeout=timeout)
            el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            el.click()
            return True
        except TimeoutException:
            continue
        except Exception:
            continue

    return False


def run_download_job(
    cfg: dict,
    codes: list[str],
    lista_id: str,  # P5, P12, P17, P22
    on_status: Optional[Callable[[dict], None]] = None,
    stop_event: Optional[threading.Event] = None,
):
    """
    Ejecuta el flujo completo de descargas para una lista de códigos.
    on_status se usará luego para reportar estado a la web.
    """
    # Asegurar que Chrome use el display virtual (Xvfb :99) en el servidor
    os.environ.setdefault("DISPLAY", ":99")
    # Que solo el Chrome que lanza este proceso use español (hereda al ser hijo); no cambia el default del servidor.
    # En el servidor debe existir el locale: sudo locale-gen es_CL.UTF-8 && sudo update-locale
    os.environ["LANG"] = "es_CL.UTF-8"
    os.environ["LC_TIME"] = "es_CL.UTF-8"

    startValue = cfg["startValue"]
    endValue = cfg["endValue"]
    SUBFOLDER = cfg["SUBFOLDER"]

    if not codes:
        print("No codes provided.")
        return

    today = datetime.utcnow().date().isoformat()
    download_dir = downloads_folder_for_subfolder(SUBFOLDER)
    print("Download directory:", download_dir)

    # --- Resolve BASE DEST DIRS ---
    base_dirs: list[Path] = []

    # Prioridad a rutas absolutas si están definidas
    if "BASE_DEST_DIRS" in cfg:
        base_dirs = [Path(p) for p in cfg.get("BASE_DEST_DIRS", [])]
    elif "BASE_DEST_DIRS_REL" in cfg and "SHARED_ROOT_NAME" in cfg:
        shared_root = Path.home() / cfg["SHARED_ROOT_NAME"]
        base_dirs = [shared_root / Path(rel) for rel in cfg.get("BASE_DEST_DIRS_REL", [])]
        print("DEBUG shared_root:", shared_root)

    print("DEBUG base_dirs:")
    for b in base_dirs:
        print(" -", b, "exists?", b.exists())

    def _dest_root_for_lista(lista: str) -> Path | None:
        """Devuelve la carpeta raíz de destino según la lista (P5, P12, P17, P22)."""
        lista = (lista or "").upper()
        for base in base_dirs:
            name = base.name.upper()
            if lista == "P5" and ("P5" in name or "5 POZOS" in name):
                return base
            if lista == "P12" and "P12" in name:
                return base
            if lista == "P17" and "P17" in name:
                return base
            if lista == "P22" and "P22" in name:
                return base
        return None

    chrome_options = Options()
    prefs = {
        "download.default_directory": str(download_dir.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        # Forzar español para el contenido web (calendario y validación de fechas DD/MM en el portal MOP)
        "intl.accept_languages": "es-CL,es,en",
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Ajustes para Linux/servidor (sin --headless para que se vea en noVNC)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--window-position=0,0")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    # Idioma de la interfaz y del contenido (evita validación MM/DD en el portal MOP)
    chrome_options.add_argument("--lang=es-CL")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(600)
    wait = WebDriverWait(driver, 30)

    lista_to_pozos_map = {
        "P5": "data/instalacion_cod_obra_titular_P5.txt",
        "P12": "data/instalacion_cod_obra_titular_P12.txt",
        "P17": "data/instalacion_cod_obra_titular_P17.txt",
        "P22": "data/instalacion_cod_obra_titular_P22.txt",
    }
    pozos_map_path = lista_to_pozos_map.get(lista_id)
    if not pozos_map_path:
        raise ValueError(f"No hay mapa de pozos configurado para lista '{lista_id}'")
    pozos_map = load_pozos_map(pozos_map_path)
    print("DEBUG pozos_map size:", len(pozos_map))

    try:
        # initial check of what is missing
        missing_codes = []
        for code in codes:
            expected = expected_filename_for(code, startValue, endValue, today)
            found = find_existing_files_for_code(download_dir, code, expected)

            if found:
                existing_file = found[0]
                print(f"✔ exists for {code}: {existing_file.name}")

                moved = move_report_to_destination(
                    renamed_file=existing_file,
                    base_dirs=base_dirs,
                    ob_code=code,
                    start=startValue,
                    end=endValue,
                    pozos_map=pozos_map,
                )

                if moved:
                    print(f"Moved existing file to: {moved}")
                else:
                    print(
                        f"WARNING: No destination folder found for {code}. "
                        f"File left at: {existing_file}"
                    )
            else:
                missing_codes.append(code)

        print(f"Missing codes: {len(missing_codes)}")

        cancelled = False
        while missing_codes:
            if stop_event and stop_event.is_set():
                print("Detención solicitada por el usuario.")
                cancelled = True
                break
            code = missing_codes.pop(0)
            expected_fn = expected_filename_for(code, startValue, endValue, today)
            print(f"\nProcessing code: {code} -> expect: {expected_fn}")

            # Notificar inicio de procesamiento
            if on_status:
                on_status({
                    "type": "pozo_update",
                    "codigo": code,
                    "estado": "En proceso",
                    "mensaje": "",
                })

            driver.get(ROOT1)

            try:
                print("Waiting for page to finish loading…")
                wait_page_loaded(driver, timeout=30)
                print("Page fully loaded.")
            except Exception:
                raise Exception("Page did not fully load...")

            time.sleep(1)

            # Refresh until CAPTCHA loads
            MAX_REFRESH = 30
            attempt = 0
            while True:
                if stop_event and stop_event.is_set():
                    cancelled = True
                    break
                attempt += 1
                print(f"Checking for CAPTCHA (attempt {attempt}/{MAX_REFRESH})")

                captcha_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    "iframe[src*='google.com/recaptcha']",
                )
                if captcha_elements:
                    print("CAPTCHA element detected (loaded).")
                    break

                if attempt >= MAX_REFRESH:
                    print("CAPTCHA did not appear after max retries.")
                    break

                print("Captcha NOT found → refreshing page...")
                driver.refresh()
                time.sleep(2)

            if cancelled:
                break

            # Wait until user SOLVES the CAPTCHA
            print("Waiting for user to solve CAPTCHA...")
            while True:
                if stop_event and stop_event.is_set():
                    cancelled = True
                    break
                token_elems = driver.find_elements(
                    By.CSS_SELECTOR,
                    "textarea[name='g-recaptcha-response'], "
                    "input[name='g-recaptcha-response'], "
                    "input[name*='recaptcha-response']",
                )

                captcha_token = None
                for el in token_elems:
                    value = el.get_attribute("value")
                    if value and value.strip():
                        captcha_token = value.strip()
                        break

                if captcha_token:
                    print("CAPTCHA solved! Token:", captcha_token[:20], "...")
                    break

                print("User has NOT solved CAPTCHA yet...")
                time.sleep(5)

            if cancelled:
                break

            print("Continuing automation...")

            # Input codigoObra
            try:
                codigo_input = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input[name="codigoObra"]')
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", codigo_input
                )
                codigo_input.clear()
                codigo_input.send_keys(code)
                driver.execute_script(
                    """
                    const el = arguments[0];
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                """,
                    codigo_input,
                )
            except Exception as e:
                print("Could not find codigoObra input:", e)
                continue

            # Click Buscar (wait overlay gone first)
            try:
                wait_overlay_gone(driver, timeout=30)
                buscar_btn = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(@class,'buttons-nav') and "
                            "contains(@class,'btn-primary') and "
                            "normalize-space(text())='Buscar']",
                        )
                    )
                )
                buscar_btn.click()
            except Exception:
                try:
                    wait_overlay_gone(driver, timeout=30)
                    btn = driver.find_element(
                        By.XPATH, "//button[normalize-space()='Buscar']"
                    )
                    btn.click()
                except Exception as e:
                    print("Could not click Buscar button:", e)
                    continue

            # Wait results and click first matching link
            try:
                time.sleep(CLICK_NAV_WAIT)
                wait_overlay_gone(driver, timeout=30)

                anchors = driver.find_elements(
                    By.XPATH,
                    f"//a[contains(normalize-space(.), '{code}')]",
                )
                if not anchors:
                    anchors = driver.find_elements(
                        By.XPATH,
                        f"//a[contains(normalize-space(.), '{code.split('-')[-1]}')]",
                    )

                if not anchors:
                    print(
                        f"No result link found for {code} after search. "
                        f"Skipping for now."
                    )
                    missing_codes.append(code)
                    if on_status:
                        on_status({
                            "type": "pozo_update",
                            "codigo": code,
                            "estado": "Error",
                            "mensaje": "No se encontró resultado en MOP",
                        })
                    continue

                anchors[0].click()
                print("Clicked result link.")
            except Exception as e:
                print("Error clicking result link:", e)
                missing_codes.append(code)
                continue

            # Click Mediciones (robust)
            time.sleep(2)
            if not click_mediciones(driver, timeout=15):
                print("Could not click Mediciones: not found/clickable.")
                try:
                    driver.save_screenshot(f"debug_{code}_mediciones.png")
                    Path(f"debug_{code}_mediciones.html").write_text(
                        driver.page_source,
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                missing_codes.append(code)
                if on_status:
                    on_status({
                        "type": "pozo_update",
                        "codigo": code,
                        "estado": "Error",
                        "mensaje": "No se pudo abrir Mediciones",
                    })
                continue
            print("Clicked Mediciones")

            # Fill dates
            try:
                start_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'input[name="inicio_periodo"]')
                    )
                )
                end_el = driver.find_element(
                    By.CSS_SELECTOR, 'input[name="fin_periodo"]'
                )

                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", start_el
                )
                # El portal usa máscara DD/MM/YYYY: hay que enviar en ese orden (con / o -)
                # Envío DD-MM-YYYY para que se vea bien en pantalla (01-03-2026, 11-03-2026)
                start_el.clear()
                start_el.send_keys(startValue)
                driver.execute_script(
                    """
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                    start_el,
                )

                end_el.clear()
                end_el.send_keys(endValue)
                driver.execute_script(
                    """
                    arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                    arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                """,
                    end_el,
                )

                time.sleep(2)
                print(f"Filled dates {startValue} -> {endValue}")
            except Exception as e:
                print("Could not set period inputs:", e)
                missing_codes.append(code)
                if on_status:
                    on_status({
                        "type": "pozo_update",
                        "codigo": code,
                        "estado": "Error",
                        "mensaje": "Error al configurar fechas",
                    })
                continue

            # Export
            try:
                wait_overlay_gone(driver, timeout=30)
                export_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(normalize-space(.), "
                            "'Exportar a excel')]",
                        )
                    )
                )
                export_btn.click()
                print("Clicked Exportar a excel")
            except Exception as e:
                print("Could not click Exportar a excel:", e)
                missing_codes.append(code)
                if on_status:
                    on_status({
                        "type": "pozo_update",
                        "codigo": code,
                        "estado": "Error",
                        "mensaje": "Error al exportar a Excel",
                    })
                continue

            print("Waiting for download...")
            renamed = wait_for_new_xls_and_rename(download_dir, expected_fn)

            if renamed:
                print(f"Downloaded & renamed to: {renamed.name}")

                # Destino basado solo en la lista (P5, P12, P17, P22)
                dest_root = _dest_root_for_lista(lista_id)
                if dest_root is None:
                    print("WARNING: No destination root found for lista", lista_id)
                    moved = None
                else:
                    year = parse_year_from_period(startValue, endValue)
                    target_dir = dest_root / str(year)
                    target_dir.mkdir(parents=True, exist_ok=True)

                    target_path = target_dir / renamed.name
                    if target_path.exists():
                        timestamp = datetime.now().strftime("%H%M%S")
                        target_path = target_dir / f"{renamed.stem}_{timestamp}{renamed.suffix}"

                    renamed.replace(target_path)
                    moved = target_path
                if moved:
                    print(f"Moved to: {moved}")
                    if on_status:
                        on_status({
                            "type": "pozo_update",
                            "codigo": code,
                            "estado": "OK",
                            "mensaje": f"Movido a {moved}",
                        })
                else:
                    print(
                        f"WARNING: No destination folder found for {code}. "
                        f"File left at: {renamed}"
                    )
                    if on_status:
                        on_status({
                            "type": "pozo_update",
                            "codigo": code,
                            "estado": "Error",
                            "mensaje": "No se encontró carpeta destino; quedó en descargas",
                        })
            else:
                print(f"Download for {code} did not complete in time.")
                missing_codes.append(code)
                if on_status:
                    on_status({
                        "type": "pozo_update",
                        "codigo": code,
                        "estado": "Error",
                        "mensaje": "La descarga no se completó a tiempo",
                    })

        print("\nAll missing codes processed. Exiting." if not cancelled else "\nDescarga detenida por el usuario.")
        if on_status:
            on_status({"type": "job_cancelled" if cancelled else "job_finished"})
    finally:
        driver.quit()