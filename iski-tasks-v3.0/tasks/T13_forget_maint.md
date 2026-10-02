# T13 — F_forget {Keep,Archive} + F_archive (async)
DEPENDS: T11
FILES: src/iski/memory/{forgetting,maintenance}.py, tests/unit/test_forgetting.py, tests/unit/test_maintenance.py
СОДЕРЖИМОЕ:
- forget_decision(w,forget_rho,imp,w_min,th_forget,th_I)->"archive"|"keep": archive если (w<w_min and imp<th_I) или (w<w_min and forget_rho>th_forget)
- archive_sweep(items,tick,T_archive)->[i]: status==1 and (tick-last_access)>T_archive
МАТЕМАТИКА: lifecycle Active->Archive->PhysicalDelete; прямой Active->PhysicalDelete запрещён.
ТЕСТЫ: таблица решений (4 кейса); sweep удаляет только status==1 и старые; активный элемент никогда не в списке.
DoD: 2 теста зелёные.
NEXT: T14
