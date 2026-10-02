# T21 — Финальный гейт и упаковка архива
DEPENDS: T01..T20
FILES: CHECKLIST.md (заполненный), iski-m0-v3.0.tar.gz или .zip, sha256
ЛОГИКА: make test; make lint; make run-m0; собрать plots; заполнить CHECKLIST по всем T;
упаковка (tar или zipfile) без venv/pycache; sha256sum.
DoD: все строки CHECKLIST зелёные либо имеют M0-issue; архив и хеш существуют; отчёт куратору: вердикт V1, список issues, план M1.
NEXT: — (конец)
