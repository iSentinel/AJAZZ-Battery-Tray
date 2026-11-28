import Foundation

/// UI-only strings; HID diagnostics and persisted data keep stable English keys.
enum AppText {
    private static let translations: [String: [String: String]] = [
        "Checking 2.4 GHz receiver…": [
            "ru": "Проверка приёмника 2,4 ГГц…",
            "uk": "Перевірка приймача 2,4 ГГц…"],
        "Refresh now": ["ru": "Обновить сейчас", "uk": "Оновити зараз"],
        "Battery history chart...": [
            "ru": "График заряда...", "uk": "Графік заряду..."],
        "Open battery history folder...": [
            "ru": "Открыть папку истории...", "uk": "Відкрити теку історії..."],
        "Diagnostic session": ["ru": "Сеанс диагностики", "uk": "Сеанс діагностики"],
        "Snapshots": ["ru": "Снимки", "uk": "Знімки"],
        "Start diagnostic session": ["ru": "Начать сеанс диагностики", "uk": "Почати сеанс діагностики"],
        "Capture baseline": ["ru": "Снять исходное состояние", "uk": "Зняти початковий стан"],
        "Mark 2.4 GHz selected": ["ru": "Отметить выбор 2,4 ГГц", "uk": "Позначити вибір 2,4 ГГц"],
        "Mark Bluetooth selected": ["ru": "Отметить выбор Bluetooth", "uk": "Позначити вибір Bluetooth"],
        "Mark sleep": ["ru": "Отметить сон", "uk": "Позначити сон"],
        "Mark wake": ["ru": "Отметить пробуждение", "uk": "Позначити пробудження"],
        "Capture another snapshot": ["ru": "Снять ещё один снимок", "uk": "Зняти ще один знімок"],
        "Save diagnostic session...": ["ru": "Сохранить сеанс диагностики...", "uk": "Зберегти сеанс діагностики..."],
        "Discard diagnostic session": ["ru": "Удалить сеанс диагностики", "uk": "Видалити сеанс діагностики"],
        "Discard all session snapshots?": ["ru": "Удалить все снимки сеанса?", "uk": "Видалити всі знімки сеансу?"],
        "Snapshot added": ["ru": "Снимок добавлен", "uk": "Знімок додано"],
        "Snapshot not added; wait a second or check session limits": ["ru": "Снимок не добавлен; подождите секунду или проверьте лимиты сеанса", "uk": "Знімок не додано; зачекайте секунду або перевірте ліміти сеансу"],
        "Session may contain reply bytes. Review before sharing.": ["ru": "Сеанс может содержать байты ответа. Проверьте перед отправкой.", "uk": "Сеанс може містити байти відповіді. Перевірте перед надсиланням."],
        "Add report to diagnostic session": ["ru": "Добавить отчёт в сеанс", "uk": "Додати звіт до сеансу"],
        "Cancel HID diagnostics": ["ru": "Отменить HID-диагностику", "uk": "Скасувати HID-діагностику"],
        "Cancelling HID diagnostics...": ["ru": "Отмена HID-диагностики...", "uk": "Скасування HID-діагностики..."],
        "Running HID diagnostics...": ["ru": "Выполняется HID-диагностика...", "uk": "Виконується HID-діагностика..."],
        "Run HID diagnostics...": ["ru": "Запустить HID-диагностику...", "uk": "Запустити HID-діагностику..."],
        "Save diagnostic report...": ["ru": "Сохранить отчёт...", "uk": "Зберегти звіт..."],
        "Close diagnostic report": ["ru": "Закрыть", "uk": "Закрити"],
        "Unable to save diagnostic report": ["ru": "Не удалось сохранить новый файл отчёта", "uk": "Не вдалося зберегти новий файл звіту"],
        "Diagnostic busy; try again after the current read": ["ru": "Идёт опрос; повторите после завершения", "uk": "Триває опитування; повторіть після завершення"],
        "HID diagnostic consent": ["en": "F7/05 query, up to 8 seconds. Report includes first 8 reply bytes. No RTC or configuration writes. Review before sharing.", "ru": "Опрос F7/05, до 8 секунд. Отчёт содержит первые 8 байт ответа. Без RTC и настроек. Проверьте перед отправкой.", "uk": "Опитування F7/05, до 8 секунд. Звіт містить перші 8 байтів відповіді. Без RTC і налаштувань. Перевірте перед надсиланням."],
        "Device diagnostics...": [
            "ru": "Диагностика устройства...", "uk": "Діагностика пристрою..."],
        "Check connected Bluetooth battery...": [
            "ru": "Проверить батарею Bluetooth...", "uk": "Перевірити батарею Bluetooth..."],
        "Copy diagnostic report": [
            "ru": "Копировать отчёт диагностики", "uk": "Копіювати звіт діагностики"],
        "Settings": ["ru": "Настройки", "uk": "Налаштування"],
        "Application icon": ["ru": "Иконка приложения", "uk": "Значок застосунку"],
        "Tray icon color": ["ru": "Цвет иконки", "uk": "Колір значка"],
        "Mouse-shaped tray icon": ["ru": "Значок мыши", "uk": "Значок миші"],
        "Orange": ["ru": "Оранжевый", "uk": "Помаранчевий"],
        "White": ["ru": "Белый", "uk": "Білий"],
        "Black": ["ru": "Чёрный", "uk": "Чорний"],
        "Blue": ["ru": "Синий", "uk": "Синій"],
        "Notifications": ["ru": "Уведомления", "uk": "Сповіщення"],
        "Low battery notifications": [
            "ru": "Уведомления о низком заряде", "uk": "Сповіщення про низький заряд"],
        "Battery notification thresholds": [
            "ru": "Пороги заряда", "uk": "Пороги заряду"],
        "Below %d%%": ["ru": "Ниже %d%%", "uk": "Нижче %d%%"],
        "Notify on receiver disconnect": [
            "ru": "Уведомлять об отключении приёмника",
            "uk": "Сповіщати про відключення приймача"],
        "Record battery history": [
            "ru": "Записывать историю заряда", "uk": "Записувати історію заряду"],
        "Refresh interval": [
            "ru": "Интервал обновления", "uk": "Інтервал оновлення"],
        "%d seconds": ["ru": "%d сек.", "uk": "%d с"],
        "Sync dock time now": [
            "ru": "Синхронизировать часы док-станции",
            "uk": "Синхронізувати годинник док-станції"],
        "Auto-sync dock clock (5 min)": [
            "ru": "Автосинхронизация часов (5 мин.)",
            "uk": "Автосинхронізація годинника (5 хв)"],
        "Dock clock: not yet synchronized": [
            "ru": "Часы док-станции: не синхронизированы",
            "uk": "Годинник док-станції: не синхронізовано"],
        "Dock clock: command sent at %@": [
            "ru": "Часы док-станции: команда отправлена в %@",
            "uk": "Годинник док-станції: команду надіслано о %@"],
        "Dock clock: unable to send at %@": [
            "ru": "Часы док-станции: ошибка отправки в %@",
            "uk": "Годинник док-станції: помилка надсилання о %@"],
        "Start at login": [
            "ru": "Запускать при входе в систему",
            "uk": "Запускати під час входу в систему"],
        "Start at login (approval needed)": [
            "ru": "Автозапуск (нужно разрешение)",
            "uk": "Автозапуск (потрібен дозвіл)"],
        "Open Login Items settings...": [
            "ru": "Открыть настройки автозапуска...",
            "uk": "Відкрити налаштування автозапуску..."],
        "Language": ["ru": "Язык", "uk": "Мова"],
        "Diagnostics": ["ru": "Диагностика", "uk": "Діагностика"],
        "Quit AJAZZ Battery Tray": [
            "ru": "Выйти из AJAZZ Battery Tray",
            "uk": "Вийти з AJAZZ Battery Tray"],
        "AJAZZ APEX receiver not found": [
            "ru": "Приёмник AJAZZ APEX не найден",
            "uk": "Приймач AJAZZ APEX не знайдено"],
        "No charge readings in this period": [
            "ru": "За этот период нет измерений заряда",
            "uk": "За цей період немає вимірювань заряду"],
        "Last verified USB sample (session): %@": [
            "ru": "Последнее подтверждённое USB-измерение (сеанс): %@",
            "uk": "Останнє підтверджене USB-вимірювання (сеанс): %@"],
        "HID read timed out": [
            "ru": "Тайм-аут чтения HID",
            "uk": "Час очікування читання HID вичерпано"
        ],
        "Cannot check USB receiver access": [
            "ru": "Не удалось проверить доступ к USB-приёмнику",
            "uk": "Не вдалося перевірити доступ до USB-приймача"],
        "Receiver HID collection not supported": [
            "ru": "HID-интерфейс приёмника не поддерживается",
            "uk": "HID-інтерфейс приймача не підтримується"],
        "Receiver found; battery status unavailable": [
            "ru": "Приёмник найден, заряд неизвестен",
            "uk": "Приймач знайдено, заряд невідомий"],
        "Unable to copy diagnostic report": [
            "ru": "Не удалось скопировать отчёт",
            "uk": "Не вдалося скопіювати звіт"],
        "The macOS clipboard is unavailable.": [
            "ru": "Буфер обмена macOS недоступен.",
            "uk": "Буфер обміну macOS недоступний."],
        "AJAZZ APEX — Device diagnostics": [
            "ru": "AJAZZ APEX — Диагностика устройства",
            "uk": "AJAZZ APEX — Діагностика пристрою"],
        "Unable to change Start at Login": [
            "ru": "Не удалось изменить автозапуск",
            "uk": "Не вдалося змінити автозапуск"],
        "Install the app in Applications, then try again.": [
            "ru": "Переместите программу в «Программы» и повторите.",
            "uk": "Перемістіть програму до «Програми» й повторіть."],
        "AJAZZ APEX: low battery": [
            "ru": "AJAZZ APEX: низкий заряд",
            "uk": "AJAZZ APEX: низький заряд"],
        "Mouse battery is at %d%%.": [
            "ru": "Заряд мыши — %d%%.", "uk": "Заряд миші — %d%%."],
        "AJAZZ APEX: receiver disconnected": [
            "ru": "AJAZZ APEX: приёмник отключён",
            "uk": "AJAZZ APEX: приймач відключено"],
        "The 2.4 GHz / 8K receiver is no longer detected.": [
            "ru": "Приёмник 2,4 ГГц / 8K больше не обнаружен.",
            "uk": "Приймач 2,4 ГГц / 8K більше не виявлено."],
        "AJAZZ APEX — Battery history": [
            "ru": "AJAZZ APEX — История заряда",
            "uk": "AJAZZ APEX — Історія заряду"],
        "Last 24 hours": ["ru": "Последние 24 часа", "uk": "Останні 24 години"],
        "Last 7 days": ["ru": "Последние 7 дней", "uk": "Останні 7 днів"],
        "Last 30 days": ["ru": "Последние 30 дней", "uk": "Останні 30 днів"],
        "Refresh": ["ru": "Обновить", "uk": "Оновити"],
        "Open CSV folder": [
            "ru": "Открыть папку CSV", "uk": "Відкрити теку CSV"],
        "No observations for the selected period": [
            "ru": "За выбранный период нет измерений",
            "uk": "За вибраний період немає вимірювань"],
        "disconnected": ["ru": "приёмник отключён", "uk": "приймач відключено"],
        "unavailable": ["ru": "заряд неизвестен", "uk": "заряд невідомий"],
        "Unable to read battery history": [
            "ru": "Не удалось прочитать историю заряда",
            "uk": "Не вдалося прочитати історію заряду"],
        "no data": ["ru": "нет данных", "uk": "немає даних"],
        "Latest: %@  •  Minimum: %@": [
            "ru": "Последний: %@  •  Минимум: %@",
            "uk": "Останній: %@  •  Мінімум: %@"],
        "Receiver absent: %d  •  %d observations": [
            "ru": "Нет связи: %d  •  %d измерений",
            "uk": "Немає зв'язку: %d  •  %d вимірювань"],
        "AJAZZ APEX — Bluetooth battery check": [
            "ru": "AJAZZ APEX — Проверка Bluetooth",
            "uk": "AJAZZ APEX — Перевірка Bluetooth"],
        "Read selected battery": ["ru": "Прочитать заряд", "uk": "Зчитати заряд"],
        "Find connected AJAZZ mice": [
            "ru": "Найти подключённые мыши AJAZZ",
            "uk": "Знайти підключені миші AJAZZ"],
        "Choose Find to inspect connected mice.": [
            "ru": "Нажмите «Найти», чтобы проверить мышь.",
            "uk": "Натисніть «Знайти», щоб перевірити мишу."],
        "Manual check of already connected AJAZZ Bluetooth mice.": [
            "ru": "Проверка уже подключённых мышей AJAZZ по Bluetooth.",
            "uk": "Перевірка вже підключених мишей AJAZZ через Bluetooth."],
        "No scanning, pairing, background polling or settings writes.": [
            "ru": "Без сканирования, сопряжения и изменения настроек.",
            "uk": "Без сканування, спарювання та зміни налаштувань."],
        "Checking Bluetooth access...": [
            "ru": "Проверка доступа Bluetooth...", "uk": "Перевірка доступу Bluetooth..."],
        "Bluetooth is not available or permission is denied.": [
            "ru": "Bluetooth недоступен или нет разрешения.",
            "uk": "Bluetooth недоступний або немає дозволу."],
        "Enable Bluetooth and grant this app Bluetooth access.": [
            "ru": "Включите Bluetooth и разрешите приложению доступ.",
            "uk": "Увімкніть Bluetooth і дозвольте програмі доступ."],
        "No connected AJAZZ mouse exposing Battery Service (180F).": [
            "ru": "Нет подключённой мыши AJAZZ с сервисом 180F.",
            "uk": "Немає підключеної миші AJAZZ із сервісом 180F."],
        "Select a connected AJAZZ mouse to read Battery Level.": [
            "ru": "Выберите мышь, чтобы прочитать заряд.",
            "uk": "Виберіть мишу, щоб зчитати заряд."],
        "Reading Battery Level from selected mouse...": [
            "ru": "Чтение заряда выбранной мыши...",
            "uk": "Зчитування заряду вибраної миші..."],
        "Battery Service timed out or is unavailable.": [
            "ru": "Время ожидания истекло или сервис недоступен.",
            "uk": "Час очікування вичерпано або сервіс недоступний."],
        "Selected mouse could not be connected for a read.": [
            "ru": "Не удалось подключиться к выбранной мыши.",
            "uk": "Не вдалося підключитися до вибраної миші."],
        "Standard Battery Service is not readable.": [
            "ru": "Стандартный сервис батареи недоступен для чтения.",
            "uk": "Стандартний сервіс батареї недоступний для зчитування."],
        "Battery Level (2A19) is not exposed.": [
            "ru": "Характеристика заряда (2A19) недоступна.",
            "uk": "Характеристика заряду (2A19) недоступна."],
        "No valid Battery Level was returned.": [
            "ru": "Действительный заряд не получен.",
            "uk": "Дійсний заряд не отримано."],
        "Bluetooth battery: %d%% (experimental)": [
            "ru": "Заряд Bluetooth: %d%% (экспериментально)",
            "uk": "Заряд Bluetooth: %d%% (експериментально)"]
    ]

    static func normalize(_ code: String?) -> String {
        if code == "ru" { return "ru" }
        if code == "uk" { return "uk" }
        return "en"
    }

    static var language: String {
        normalize(UserDefaults.standard.string(forKey: "UILanguage"))
    }

    static func choose(_ code: String) {
        UserDefaults.standard.set(normalize(code), forKey: "UILanguage")
    }

    static func text(_ english: String) -> String {
        translations[english]?[language] ?? english
    }

    static func format(_ english: String, _ values: CVarArg...) -> String {
        String(format: text(english), locale: Locale(identifier: language),
               arguments: values)
    }
}
