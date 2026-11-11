"""Restore to a new, retained site. Never restore over or delete the source site."""

import json
import os
import secrets
import subprocess
import uuid
from pathlib import Path

SOURCE = "av.localhost"


def bench(*args, capture=False):
    result = subprocess.run(["bench", *args], check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout if capture else None


def execute(site, method):
    output = bench("--site", site, "execute", method, capture=True)
    return json.loads(output.strip().splitlines()[-1])


def main():
    backup = execute(SOURCE, "av_platform.evidence.backup")
    target = f"av-restore-{uuid.uuid4().hex[:12]}.localhost"
    bench("new-site", target, "--db-root-username", "root", "--db-root-password",
          os.environ["DB_ROOT_PASSWORD"], "--admin-password", secrets.token_hex(24),
          "--mariadb-user-host-login-scope=%")
    config_path = Path("sites") / target / "site_config.json"
    config = json.loads(config_path.read_text())
    original = json.loads(Path(backup["config"]).read_text())
    config.update({"av_prototype": 1, "pause_scheduler": 1, "mute_emails": 1})
    if original.get("installed_apps"):
        config["installed_apps"] = original["installed_apps"]
    if original.get("encryption_key"):
        config["encryption_key"] = original["encryption_key"]
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    bench("--site", target, "restore", backup["database"], "--force",
          "--db-root-username", "root", "--db-root-password", os.environ["DB_ROOT_PASSWORD"],
          "--with-public-files", backup["public_files"],
          "--with-private-files", backup["private_files"])
    bench("--site", target, "migrate")
    restored = execute(target, "av_platform.evidence.manifest")
    result = {"source": SOURCE, "restored_site": target,
              "passed": backup["manifest"] == restored,
              "scope": "handover snapshots, linked quotations/projects, private canary content"}
    output_dir = Path("sites") / SOURCE / "private" / "backups"
    (output_dir / f"{target}-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    if not result["passed"]:
        raise RuntimeError("Restore comparison failed. Both sites retained for diagnosis.")


if __name__ == "__main__":
    main()
