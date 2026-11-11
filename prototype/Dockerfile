# Upstream release plus immutable multi-platform image digest, verified 2026-11-05.
FROM frappe/erpnext:v16.53.0@sha256:b961d69ed3265f44f712f40be58a3e6a22c8662f61a7e1a8097765534e3e9be2

COPY --chown=frappe:0 apps/av_platform /home/frappe/frappe-bench/apps/av_platform
RUN bench pip install --no-cache-dir -e apps/av_platform \
    && printf '\nav_platform\n' >> sites/apps.txt \
    && bench build --app av_platform

COPY --chown=frappe:0 prototype/site.py prototype/restore_check.py /opt/av-prototype/
