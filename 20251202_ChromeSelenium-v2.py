from core.config import load_config, load_codes
from core.mop_client import run_download_job


def main():
    cfg = load_config("data/config.json")
    codes = load_codes("data/pozosADescargarP5.txt")

    if not codes:
        print("No codes found in data/pozosADescargarP5.txt")
        return

    run_download_job(cfg, codes, "P5")


if __name__ == "__main__":
    main()
