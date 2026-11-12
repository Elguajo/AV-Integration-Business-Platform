"""Idempotent, fail-fast initialization inside the isolated container."""

import json
import os
import subprocess
from pathlib import Path

SITE = "av.localhost"


def bench(*args):
    subprocess.run(["bench", *args], check=True)


def main():
    config = Path("sites/common_site_config.json")
    values = json.loads(config.read_text()) if config.exists() else {}
    values.update({
        "db_host": "db", "db_port": 3306,
        "redis_cache": "redis://redis-cache:6379",
        "redis_queue": "redis://redis-queue:6379",
        "redis_socketio": "redis://redis-queue:6379", "socketio_port": 9000,
    })
    config.write_text(json.dumps(values, indent=2) + "\n")
    # Shared volume must list the custom app even when reused with a newly built image.
    Path("sites/apps.txt").write_text("frappe\nerpnext\nav_platform\n")
    site_config = Path("sites") / SITE / "site_config.json"
    if not site_config.exists():
        bench("new-site", SITE, "--db-root-username", "root", "--db-root-password",
              os.environ["DB_ROOT_PASSWORD"], "--admin-password", os.environ["ADMIN_PASSWORD"],
              "--mariadb-user-host-login-scope=%", "--install-app", "erpnext")
    bench("--site", SITE, "set-config", "av_prototype", "1", "--parse")
    # --parse uses ast.literal_eval, so booleans must be Python literals.
    bench("--site", SITE, "set-config", "mute_emails", "True", "--parse")
    bench("--site", SITE, "install-app", "av_platform")
    bench("--site", SITE, "migrate")
    bench("--site", SITE, "set-config", "allow_tests", "True", "--parse")
    bench("use", SITE)
    bench("version", "--format", "json")


if __name__ == "__main__":
    main()
