namespace AjazzBatteryTray;

/// <summary>UI-only translations; protocol diagnostics remain in English.</summary>
public static class UiText
{
    private static readonly Dictionary<string, (string Ru, string Uk)> Messages = new()
    {
        ["No charge readings in this period"] = ("За этот период нет измерений заряда", "За цей період немає вимірювань заряду"),
        ["Capturing HID report (up to {0} s)…"] = ("Сбор отчёта HID (до {0} с)…", "Збирання звіту HID (до {0} с)…"),
        ["HID capture timed out. No battery reading was verified."] = ("Время сбора отчёта HID истекло. Получить достоверный заряд не удалось.", "Час збирання звіту HID вичерпано. Отримати достовірний рівень заряду не вдалося."),
        ["HID read timed out"] = ("Тайм-аут чтения HID", "Час очікування читання HID вичерпано"),
        ["HID interface busy"] = ("HID-интерфейс занят", "HID-інтерфейс зайнятий"),
        ["HID interface unavailable"] = ("HID-интерфейс недоступен", "HID-інтерфейс недоступний"),
        ["Receiver disconnected"] = ("Приёмник отключён", "Приймач відключено"),
        ["Receiver present, no fresh charge"] = ("Приёмник подключён, свежих данных нет", "Приймач підключено, свіжих даних немає"),
        ["{0}% (unverified)"] = ("{0}% (не подтверждено)", "{0}% (не підтверджено)"),
        ["Last verified {0}"] = ("Последний замер {0}", "Останній вимір {0}"),
        ["Device settings"] = ("Настройки устройства", "Налаштування пристрою"),
        ["Device Manager"] = ("Управление устройствами", "Керування пристроями"),
        ["Live monitor — existing readings only; cached values are marked."] = ("Мониторинг устройств — только полученные данные; кэш отмечен звёздочкой.", "Моніторинг пристроїв — лише отримані дані; кеш позначено зірочкою."),
        ["Device"] = ("Устройство", "Пристрій"),
        ["Transport"] = ("Подключение", "Підключення"),
        ["Status"] = ("Состояние", "Стан"),
        ["Battery"] = ("Заряд", "Заряд"),
        ["Last measurement"] = ("Последнее измерение", "Останнє вимірювання"),
        ["Not checked"] = ("Не проверено", "Не перевірено"),
        ["Monitoring disabled"] = ("Мониторинг отключён", "Моніторинг вимкнено"),
        ["Standby (USB priority)"] = ("Ожидание (приоритет USB)", "Очікування (пріоритет USB)"),
        ["Receiver status unknown"] = ("Статус приёмника неизвестен", "Стан приймача невідомий"),
        ["Disconnected"] = ("Отключено", "Відключено"),
        ["No valid reply"] = ("Нет корректного ответа", "Немає коректної відповіді"),
        ["Unverified charge field"] = ("Не подтверждено", "Не підтверджено"),
        ["Manual reading"] = ("Результат ручного запроса", "Результат ручного запиту"),
        ["Fresh reading"] = ("Свежие данные", "Свіжі дані"),
        ["Cached reading"] = ("Последние известные данные", "Останні відомі дані"),
        ["No device readings yet"] = ("Пока нет данных устройств", "Поки немає даних пристроїв"),
        ["Windows device names preview..."] = ("Предпросмотр имён устройств Windows...", "Попередній перегляд назв пристроїв Windows..."),
        ["Preview only — no Windows device names changed."] = ("Только предпросмотр — имена устройств Windows не изменены.", "Лише попередній перегляд — назви пристроїв Windows не змінено."),
        ["Model names are provisional; confirm the receiver before applying."] = ("Названия моделей предварительные; перед применением подтвердите приёмник.", "Назви моделей попередні; перед застосуванням підтвердьте приймач."),
        ["USB receiver"] = ("USB-приёмник", "USB-приймач"),
        ["Mouse HID candidate"] = ("Предполагаемый HID-интерфейс мыши", "Імовірний HID-інтерфейс миші"),
        ["Keyboard HID candidate"] = ("Предполагаемый HID-интерфейс клавиатуры", "Імовірний HID-інтерфейс клавіатури"),
        ["Current: {0}"] = ("Текущее: {0}", "Поточне: {0}"),
        ["Proposed: {0}"] = ("Предлагаемое: {0}", "Запропоноване: {0}"),
        ["No matching present USB receivers found."] = ("Подходящие подключённые USB-приёмники не найдены.", "Відповідні підключені USB-приймачі не знайдено."),
        ["Additional candidates omitted; no changes applied."] = ("Дополнительные кандидаты скрыты; изменения не внесены.", "Додаткові кандидати приховано; зміни не внесено."),
        ["Unable to read Windows device names."] = ("Не удалось прочитать имена устройств Windows.", "Не вдалося зчитати назви пристроїв Windows."),
        ["Edit local name..."] = ("Изменить имя устройства...", "Змінити назву пристрою..."),
        ["Local name only. Clear to restore the detected name."] = ("Локальное имя в приложении. Очистите поле для восстановления исходного имени.", "Локальна назва в застосунку. Очистьте поле для відновлення початкової назви."),
        ["Save local name"] = ("Сохранить имя", "Зберегти назву"),
        ["Invalid local device name."] = ("Недопустимое имя устройства.", "Неприпустима назва пристрою."),
        ["Unable to save local device name."] = ("Не удалось сохранить имя устройства.", "Не вдалося зберегти назву пристрою."),
        ["Cancel"] = ("Отмена", "Скасувати"),
        ["Show device in tray"] = ("Показывать в трее", "Показувати в треї"),
        ["Hide device in tray"] = ("Скрыть из трея", "Приховати з трея"),
        ["Tray preference"] = ("Настройка трея", "Налаштування трея"),
        ["Allowed"] = ("Разрешено", "Дозволено"),
        ["Hidden"] = ("Скрыто", "Приховано"),
        ["Unable to save device preference."] = ("Не удалось сохранить настройку устройства.", "Не вдалося зберегти налаштування пристрою."),
        ["Tray icon color..."] = ("Цвет иконки в трее...", "Колір значка в треї..."),
        ["Warning and cached colors are unchanged."] = ("Цвета предупреждений и кэша не изменяются.", "Кольори попереджень і кешу не змінюються."),
        ["Tray color green"] = ("Зелёный", "Зелений"),
        ["Tray color orange"] = ("Оранжевый", "Помаранчевий"),
        ["Tray color white"] = ("Белый", "Білий"),
        ["Tray color black"] = ("Чёрный", "Чорний"),
        ["Tray color inherit"] = ("Общий цвет", "Загальний колір"),
        ["Application icon"] = ("Иконка приложения", "Значок застосунку"),
        ["Save selected icon..."] = ("Сохранить выбранную иконку...", "Зберегти вибраний значок..."),
        ["Cannot save icon. Choose a new writable file."] =
            ("Не удалось сохранить иконку. Выберите новый доступный для записи файл.",
             "Не вдалося зберегти значок. Виберіть новий доступний для запису файл."),
        ["Default tray color"] = ("Общий цвет трея", "Загальний колір трею"),
        ["Mouse-shaped tray icon"] = ("Значок мыши в трее", "Значок миші в треї"),
        ["Tray color blue"] = ("Синий", "Синій"),
        ["Tray color purple"] = ("Фиолетовый", "Фіолетовий"),
        ["Tray color teal"] = ("Бирюзовый", "Бірюзовий"),
        ["Tray color pink"] = ("Розовый", "Рожевий"),
        ["Tray color slate"] = ("Сине-серый", "Синьо-сірий"),
        ["Save"] = ("Сохранить", "Зберегти"),
        ["Connecting..."] = ("Подключение...", "Підключення..."),
        ["Refresh now"] = ("Обновить сейчас", "Оновити зараз"),
        ["AJAZZ receivers"] = ("Приёмники AJAZZ", "Приймачі AJAZZ"),
        ["Legacy battery history..."] = ("Старая история заряда...", "Стара історія заряду..."),
        ["Separate tray icons"] = ("Отдельные иконки в трее", "Окремі значки в треї"),
        ["Battery history..."] = ("История заряда...", "Історія заряду..."),
        ["Check paired Bluetooth battery..."] = ("Проверить батарею Bluetooth...", "Перевірити батарею Bluetooth..."),
        ["Bluetooth"] = ("Bluetooth", "Bluetooth"),
        ["Disable Bluetooth monitors"] = ("Отключить мониторинг Bluetooth", "Вимкнути моніторинг Bluetooth"),
        ["Bluetooth monitor enabled for this session; independent of USB."] = ("Мониторинг Bluetooth включён на сеанс независимо от USB.", "Моніторинг Bluetooth увімкнено на сеанс незалежно від USB."),
        ["Bluetooth fallback: off"] = ("Bluetooth: отключён", "Bluetooth: вимкнено"),
        ["Bluetooth fallback: standby (USB primary)"] = ("Bluetooth: ожидание (приоритет USB)", "Bluetooth: очікування (пріоритет USB)"),
        ["Bluetooth fallback: checking battery..."] = ("Bluetooth: проверка заряда...", "Bluetooth: перевірка заряду..."),
        ["Bluetooth fallback: paused (receiver status unknown)"] = ("Bluetooth: пауза (статус приёмника неизвестен)", "Bluetooth: пауза (стан приймача невідомий)"),
        ["Disable Bluetooth tray fallback"] = ("Отключить Bluetooth-мониторинг", "Вимкнути Bluetooth-моніторинг"),
        ["Refresh Bluetooth battery now"] = ("Обновить заряд Bluetooth", "Оновити заряд Bluetooth"),
        ["Copy Bluetooth monitor status"] = ("Копировать статус Bluetooth", "Копіювати стан Bluetooth"),
        ["Copy diagnostic report"] = ("Копировать отчёт диагностики", "Копіювати звіт діагностики"),
        ["Sync dock time now"] = ("Синхронизировать часы док-станции", "Синхронізувати годинник док-станції"),
        ["Dock clock: not yet synchronized"] = ("Часы док-станции: не синхронизированы", "Годинник док-станції: не синхронізовано"),
        ["Dock clock: command sent at {0}"] = ("Часы док-станции: команда отправлена в {0}", "Годинник док-станції: команду надіслано о {0}"),
        ["Dock clock: unable to send at {0}"] = ("Часы док-станции: ошибка отправки в {0}", "Годинник док-станції: помилка надсилання о {0}"),
        ["Settings"] = ("Настройки", "Налаштування"),
        ["Notifications"] = ("Уведомления", "Сповіщення"),
        ["Low battery notifications"] = ("Уведомления о низком заряде", "Сповіщення про низький заряд"),
        ["Battery notification thresholds"] = ("Пороги заряда", "Пороги заряду"),
        ["Below {0}%"] = ("Ниже {0}%", "Нижче {0}%"),
        ["Notify on receiver disconnect"] = ("Уведомлять об отключении приёмника", "Сповіщати про відключення приймача"),
        ["Update interval"] = ("Интервал обновления", "Інтервал оновлення"),
        ["{0} seconds"] = ("{0} сек.", "{0} с"),
        ["Auto-sync dock clock (5 min)"] = ("Автосинхронизация часов (5 мин.)", "Автосинхронізація годинника (5 хв)"),
        ["Record battery history"] = ("Записывать историю заряда", "Записувати історію заряду"),
        ["Start with Windows"] = ("Запускать вместе с Windows", "Запускати разом із Windows"),
        ["Language"] = ("Язык", "Мова"),
        ["Diagnostics"] = ("Диагностика", "Діагностика"),
        ["Verify downloaded release..."] = ("Проверить скачанный релиз...", "Перевірити завантажений реліз..."),
        ["Choose the EXE and SHA-256 file from the same GitHub release."] = ("Выберите EXE и файл SHA-256 из одного релиза GitHub.", "Виберіть EXE та файл SHA-256 з одного релізу GitHub."),
        ["Choose EXE..."] = ("Выбрать EXE...", "Вибрати EXE..."),
        ["Choose SHA-256..."] = ("Выбрать SHA-256...", "Вибрати SHA-256..."),
        ["Verify checksum"] = ("Проверить контрольную сумму", "Перевірити контрольну суму"),
        ["A matching checksum is not a publisher signature. No file is executed."] = ("Совпадение хеша не является подписью издателя. Файлы не запускаются.", "Збіг хешу не є підписом видавця. Файли не запускаються."),
        ["No EXE selected."] = ("EXE не выбран.", "EXE не вибрано."),
        ["No checksum selected."] = ("Контрольная сумма не выбрана.", "Контрольну суму не вибрано."),
        ["Unsupported release filename."] = ("Неподдерживаемое имя файла релиза.", "Непідтримувана назва файлу релізу."),
        ["Choose the matching checksum file."] = ("Выберите соответствующий файл контрольной суммы.", "Виберіть відповідний файл контрольної суми."),
        ["Verifying SHA-256..."] = ("Проверка SHA-256...", "Перевірка SHA-256..."),
        ["SHA-256 matches."] = ("SHA-256 совпадает.", "SHA-256 збігається."),
        ["SHA-256 mismatch. Do not run this file."] = ("SHA-256 не совпадает. Не запускайте файл.", "SHA-256 не збігається. Не запускайте файл."),
        ["Verification failed; check the selected files."] = ("Ошибка проверки; проверьте выбранные файлы.", "Помилка перевірки; перевірте вибрані файли."),
        ["Automatic checks stopped for this session; disabling could not be saved."] = ("Автопроверка остановлена на текущий сеанс; сохранить отключение не удалось.", "Автоперевірку зупинено на поточний сеанс; зберегти вимкнення не вдалося."),
        ["Enabled"] = ("Включено", "Увімкнено"),
        ["Disabled"] = ("Отключено", "Вимкнено"),
        ["Restore previewed preferences..."] = ("Восстановить просмотренные настройки...", "Відновити переглянуті налаштування..."),
        ["Replace global preferences with the previewed values? Existing device settings and update consent are preserved. Notification preferences may resume already authorized checks."] = ("Заменить общие настройки просмотренными значениями? Настройки устройств и согласие на обновления сохраняются. Уведомления могут возобновить ранее разрешённые проверки.", "Замінити загальні налаштування переглянутими значеннями? Налаштування пристроїв і згода на оновлення зберігаються. Сповіщення можуть відновити раніше дозволені перевірки."),
        ["Restore failed; previous preferences retained."] = ("Восстановление не удалось; прежние настройки сохранены.", "Відновлення не вдалося; попередні налаштування збережено."),
        ["Global preferences restored."] = ("Общие настройки восстановлены.", "Загальні налаштування відновлено."),
        ["Local battery API..."] = ("Локальный API батарей...", "Локальний API батарей..."),
        ["Local PC only. Closing this window stops the API. No hardware commands."] = ("Только этот ПК. Закрытие окна останавливает API. Без команд устройствам.", "Лише цей ПК. Закриття вікна зупиняє API. Без команд пристроям."),
        ["Start local API"] = ("Запустить локальный API", "Запустити локальний API"),
        ["Stop local API"] = ("Остановить локальный API", "Зупинити локальний API"),
        ["Copy API token"] = ("Копировать токен API", "Копіювати токен API"),
        ["Local API stopped."] = ("Локальный API остановлен.", "Локальний API зупинено."),
        ["Local API running. Keep this window open."] = ("Локальный API работает. Оставьте окно открытым.", "Локальний API працює. Залиште вікно відкритим."),
        ["Unable to start local API; port may be in use."] = ("Не удалось запустить API; возможно, порт занят.", "Не вдалося запустити API; можливо, порт зайнятий."),
        ["Unable to copy API token."] = ("Не удалось скопировать токен API.", "Не вдалося скопіювати токен API."),
        ["Copy local battery snapshot"] = ("Копировать локальный снимок батарей", "Копіювати локальний знімок батарей"),
        ["Local battery snapshot copied."] = ("Локальный снимок батарей скопирован.", "Локальний знімок батарей скопійовано."),
        ["Unable to copy local battery snapshot."] = ("Не удалось скопировать локальный снимок батарей.", "Не вдалося скопіювати локальний знімок батарей."),
        ["Preferences backup..."] = ("Резервная копия настроек...", "Резервна копія налаштувань..."),
        ["Global preferences only. Preview does not apply settings."] = ("Только общие настройки. Предпросмотр не применяет значения.", "Лише загальні налаштування. Перегляд не застосовує значення."),
        ["Export preferences..."] = ("Экспортировать настройки...", "Експортувати налаштування..."),
        ["Preview backup..."] = ("Просмотреть резервную копию...", "Переглянути резервну копію..."),
        ["Preferences exported."] = ("Настройки экспортированы.", "Налаштування експортовано."),
        ["Export failed. Select a new file name."] = ("Ошибка экспорта. Выберите новое имя файла.", "Помилка експорту. Виберіть нову назву файлу."),
        ["Invalid or unsupported preferences backup."] = ("Повреждённая или неподдерживаемая копия настроек.", "Пошкоджена або непідтримувана копія налаштувань."),
        ["Validated global preferences"] = ("Проверенные общие настройки", "Перевірені загальні налаштування"),
        ["No settings have been changed."] = ("Настройки не изменены.", "Налаштування не змінено."),
        ["Update preferences"] = ("Настройки обновлений", "Налаштування оновлень"),
        ["Automatically check GitHub releases"] = ("Автоматически проверять релизы GitHub", "Автоматично перевіряти релізи GitHub"),
        ["Allow daily GitHub release checks? No files will be downloaded."] = ("Разрешить ежедневную проверку релизов GitHub? Файлы скачиваться не будут.", "Дозволити щоденну перевірку релізів GitHub? Файли не завантажуватимуться."),
        ["A background update check is in progress."] = ("Выполняется фоновая проверка обновлений.", "Виконується фонова перевірка оновлень."),
        ["Check for updates..."] = ("Проверить обновления...", "Перевірити оновлення..."),
        ["Installed version: {0}"] = ("Установлена версия: {0}", "Встановлено версію: {0}"),
        ["Release channel"] = ("Канал релизов", "Канал релізів"),
        ["Stable"] = ("Стабильный", "Стабільний"),
        ["Experimental (beta)"] = ("Экспериментальный (beta)", "Експериментальний (beta)"),
        ["Check now"] = ("Проверить сейчас", "Перевірити зараз"),
        ["No network request until you choose Check now."] = ("Запрос в сеть только после нажатия «Проверить сейчас».", "Запит до мережі лише після натискання «Перевірити зараз»."),
        ["Open release page"] = ("Открыть страницу релиза", "Відкрити сторінку релізу"),
        ["Checking GitHub releases..."] = ("Проверка релизов GitHub...", "Перевірка релізів GitHub..."),
        ["No newer release found in this channel."] = ("В этом канале более новая версия не найдена.", "У цьому каналі новішої версії не знайдено."),
        ["Update available: {0}"] = ("Доступно обновление: {0}", "Доступне оновлення: {0}"),
        ["Update check failed; try again later."] = ("Не удалось проверить обновления; попробуйте позже.", "Не вдалося перевірити оновлення; спробуйте пізніше."),
        ["Unable to open release page."] = ("Не удалось открыть страницу релиза.", "Не вдалося відкрити сторінку релізу."),
        ["Enable selected BLE monitor (this session)"] = ("Включить мониторинг выбранного BLE (на сеанс)", "Увімкнути моніторинг вибраного BLE (на сеанс)"),
        ["Disable selected BLE monitor"] = ("Выключить мониторинг выбранного BLE", "Вимкнути моніторинг вибраного BLE"),
        ["Read selected battery again before enabling monitoring."] = ("Повторите чтение заряда перед включением мониторинга.", "Повторіть читання заряду перед увімкненням моніторингу."),
        ["Bluetooth monitor enabled for this session; USB keeps priority."] = ("Мониторинг Bluetooth включён на сеанс; USB имеет приоритет.", "Моніторинг Bluetooth увімкнено на сеанс; USB має пріоритет."),
        ["Opted-in BLE devices"] = ("Выбранные BLE-устройства", "Вибрані BLE-пристрої"),
        ["Bluetooth monitors: {0}"] = ("Устройств Bluetooth: {0}", "Пристроїв Bluetooth: {0}"),

        ["Full APEX comparison report..."] = ("Полная диагностика APEX...", "Повна діагностика APEX..."),
        ["Device polling interval..."] = ("Интервал опроса устройства...", "Інтервал опитування пристрою..."),
        ["Use global interval ({0} seconds)"] = ("Общий интервал ({0} сек.)", "Загальний інтервал ({0} с)"),
        ["Last scheduled reading"] = ("Последнее плановое измерение", "Останнє планове вимірювання"),
        ["Device battery alerts..."] = ("Уведомления батареи устройства...", "Сповіщення батареї пристрою..."),
        ["Use global alert thresholds"] = ("Использовать общие пороги", "Використовувати загальні пороги"),
        ["Device notifications..."] = ("Уведомления устройства...", "Сповіщення пристрою..."),
        ["Use global disconnect setting"] = ("Использовать общее правило отключения", "Використовувати загальне правило відключення"),
        ["Global low-battery switch applies only to battery thresholds."] =
            ("Общий переключатель низкого заряда действует только для порогов батареи.",
             "Загальний перемикач низького заряду діє лише для порогів батареї."),
        ["Global notification switch still applies."] = ("Общий переключатель уведомлений продолжает действовать.", "Загальний перемикач сповіщень продовжує діяти."),
        ["Capture AJAZZ battery protocol..."] = ("Записать протокол батареи AJAZZ...", "Записати протокол батареї AJAZZ..."),
        ["A poll or diagnostic is running. Try again."] = ("Выполняется опрос или диагностика. Повторите попытку.", "Триває опитування або діагностика. Повторіть спробу."),
        ["Capture full vendor battery buffers locally? Close the official utility first. Review raw data before sharing."] =
            ("Записать полные буферы батареи локально? Сначала закройте оригинальную утилиту. Проверьте сырые данные перед отправкой.",
             "Записати повні буфери батареї локально? Спочатку закрийте оригінальну утиліту. Перевірте сирі дані перед надсиланням."),
        ["Extended device diagnostics..."] = ("Расширенная диагностика...", "Розширена діагностика..."),
        ["Extended device diagnostics"] = ("Расширенная диагностика", "Розширена діагностика"),
        ["Copy report"] = ("Копировать отчёт", "Копіювати звіт"),
        ["Save report..."] = ("Сохранить отчёт...", "Зберегти звіт..."),
        ["Close"] = ("Закрыть", "Закрити"),
        ["Text files (*.txt)"] = ("Текстовые файлы (*.txt)", "Текстові файли (*.txt)"),
        ["Unable to save diagnostic report."] = ("Не удалось сохранить отчёт диагностики.", "Не вдалося зберегти звіт діагностики."),
        ["Unable to collect diagnostic report."] = ("Не удалось собрать отчёт диагностики.", "Не вдалося зібрати звіт діагностики."),
        ["Device diagnostics..."] = ("Диагностика устройства...", "Діагностика пристрою..."),
        ["Open log folder"] = ("Открыть папку журналов", "Відкрити теку журналів"),
        ["Exit"] = ("Выход", "Вихід"),
        ["cached"] = ("последний заряд", "останній заряд"),
        ["AULA L99: cached {0}% at {1}; no fresh reply"] =
            ("AULA L99: последний {0}% в {1}; нового ответа нет",
             "AULA L99: останній {0}% о {1}; нової відповіді немає"),
        ["unavailable"] = ("недоступно", "недоступно"),
        ["AJAZZ APEX: low battery"] = ("AJAZZ APEX: низкий заряд", "AJAZZ APEX: низький заряд"),
        ["Mouse battery is {0}% ({1}); below {2}%." ] =
            ("Заряд мыши {0}% ({1}); ниже {2}%.", "Заряд миші {0}% ({1}); нижче {2}%."),
        ["AJAZZ APEX disconnected"] = ("AJAZZ APEX: нет связи", "AJAZZ APEX: немає зв'язку"),
        ["The 2.4 GHz receiver is no longer detected."] =
            ("Приёмник 2,4 ГГц больше не обнаружен.", "Приймач 2,4 ГГц більше не виявлено."),
        ["The Windows clipboard is currently unavailable."] =
            ("Буфер обмена Windows недоступен.", "Буфер обміну Windows недоступний."),
        ["AJAZZ APEX device diagnostics"] = ("AJAZZ APEX — диагностика устройства", "AJAZZ APEX — діагностика пристрою"),
        ["Last 24 hours"] = ("Последние 24 часа", "Останні 24 години"),
        ["Last 7 days"] = ("Последние 7 дней", "Останні 7 днів"),
        ["Last 30 days"] = ("Последние 30 дней", "Останні 30 днів"),
        ["Refresh"] = ("Обновить", "Оновити"),
        ["Open CSV folder"] = ("Открыть папку CSV", "Відкрити теку CSV"),
        ["Runtime estimate unavailable: insufficient recent discharge observations."] =
            ("Прогноз недоступен: недостаточно недавних наблюдений разряда.",
             "Прогноз недоступний: недостатньо недавніх спостережень розряду."),
        ["Observed drain: {0:N1} pp/hour | Estimated runtime: {1:N1} hours"] =
            ("Скорость разряда: {0:N1} п.п./ч | Прогноз работы: {1:N1} ч",
             "Швидкість розряду: {0:N1} в.п./год | Прогноз роботи: {1:N1} год"),
        ["Based on {0} observations over {1:N0} minutes; last measurement {2}."] =
            ("По {0} наблюдениям за {1:N0} мин; последнее измерение {2}.",
             "За {0} спостереженнями протягом {1:N0} хв; останнє вимірювання {2}."),
        ["Observed discharge: insufficient observations."] =
            ("Наблюдаемый разряд: недостаточно наблюдений.", "Спостережуваний розряд: недостатньо спостережень."),
        ["Observed discharge equivalents: {0:N2} (selected range; not battery health)."] =
            ("Наблюдаемый эквивалент разряда: {0:N2} (выбранный период; не износ батареи).",
             "Спостережуваний еквівалент розряду: {0:N2} (вибраний період; не знос батареї)."),
        ["Linear estimate at the observed rate; usage and charging may change it."] =
            ("Линейная оценка; нагрузка и зарядка могут изменить прогноз.",
             "Лінійна оцінка; навантаження та заряджання можуть змінити прогноз."),
        ["Battery history"] = ("История заряда", "Історія заряду"),
        ["Records: {0}  |  Local CSV: {1} (last 30 days)"] =
            ("Записей: {0}  |  Локальный CSV: {1} (30 дней)",
             "Записів: {0}  |  Локальний CSV: {1} (30 днів)"),
        ["System telemetry preview..."] = ("Предпросмотр системной телеметрии...", "Попередній перегляд системної телеметрії..."),
        ["Preview only — no keyboard data sent."] = ("Только предпросмотр — данные клавиатуре не отправлены.", "Лише попередній перегляд — дані клавіатурі не надіслані."),
        ["Windows CPU load: {0}"] = ("Нагрузка CPU (Windows): {0}", "Навантаження CPU (Windows): {0}"),
        ["Load: {0}; temperature: {1}"] = ("Нагрузка: {0}; температура: {1}", "Навантаження: {0}; температура: {1}"),
        ["For GPU and temperature sensors, use a running LibreHardwareMonitor local web server at 127.0.0.1:8085."] =
            ("Для GPU и температур запусти локальный веб-сервер LibreHardwareMonitor на 127.0.0.1:8085.", "Для GPU і температур запусти локальний вебсервер LibreHardwareMonitor на 127.0.0.1:8085."),
        ["AULA L99 (experimental)"] =
            ("AULA L99 (экспериментально)", "AULA L99 (експериментально)"),
        ["AULA L99: not checked"] =
            ("AULA L99: ещё не проверена", "AULA L99: ще не перевірено"),
        ["AULA L99: checking battery..."] =
            ("AULA L99: проверка заряда...", "AULA L99: перевірка заряду..."),
        ["AULA L99: dongle not found"] =
            ("AULA L99: приёмник не найден", "AULA L99: приймач не знайдено"),
        ["AULA L99: no valid battery reply"] =
            ("AULA L99: заряд неизвестен", "AULA L99: заряд невідомий"),
        ["AULA L99: HID status unknown"] =
            ("AULA L99: ошибка HID", "AULA L99: помилка HID"),
        ["AULA L99: last {0}% at {1} (unverified)"] =
            ("AULA L99: последний {0}% в {1} (модель не подтверждена)",
             "AULA L99: останній {0}% о {1} (модель не підтверджена)"),
        ["Read AULA battery once"] =
            ("Прочитать заряд AULA один раз", "Зчитати заряд AULA один раз"),
        ["Monitor AULA automatically (experimental)"] =
            ("Мониторинг AULA автоматически (экспериментально)",
             "Моніторинг AULA автоматично (експериментально)"),
        ["Copy AULA diagnostic summary"] =
            ("Копировать диагностику AULA", "Копіювати діагностику AULA"),
        ["AULA battery history..."] =
            ("История заряда AULA...", "Історія заряду AULA..."),
        ["AULA L99: low battery"] =
            ("AULA L99: низкий заряд", "AULA L99: низький заряд"),
        ["Keyboard battery is {0}%; below {1}%."] =
            ("Заряд клавиатуры {0}%; ниже {1}%.",
             "Заряд клавіатури {0}%; нижче {1}%."),
        ["AJAZZ APEX — Battery history"] = ("AJAZZ APEX — История заряда", "AJAZZ APEX — Історія заряду"),
        ["No observations yet. History is saved locally."] =
            ("Пока нет измерений. История хранится локально.", "Вимірювань ще немає. Історія зберігається локально."),
        ["No battery observations yet"] = ("Пока нет измерений заряда", "Вимірювань заряду ще немає"),
        ["Latest: {0}  |  Minimum: {1}  |  Absent: {2}  |  Unavailable: {3}"] =
            ("Последний: {0}  |  Минимум: {1}  |  Нет связи: {2}  |  Недоступно: {3}",
             "Останній: {0}  |  Мінімум: {1}  |  Немає зв'язку: {2}  |  Недоступно: {3}"),
        ["Records: {0}  |  Local CSV: battery-history.csv (last 30 days)"] =
            ("Записей: {0}  |  Локальный CSV: battery-history.csv (30 дней)",
             "Записів: {0}  |  Локальний CSV: battery-history.csv (30 днів)"),
        ["AJAZZ — Experimental Bluetooth battery check"] =
            ("AJAZZ — Проверка батареи Bluetooth", "AJAZZ — Перевірка батареї Bluetooth"),
        ["Show all paired Bluetooth devices (if mouse name is different)"] =
            ("Показать все сопряжённые устройства Bluetooth", "Показати всі спарені пристрої Bluetooth"),
        ["Copy lookup summary"] = ("Копировать результат поиска", "Копіювати результат пошуку"),
        ["Collect full diagnostics..."] = ("Собрать полную диагностику...", "Зібрати повну діагностику..."),
        ["Collect full diagnostics? Yes includes raw vendor buffers; close the official utility first. No collects existing monitoring data only. Review before sharing."] =
            ("Собрать полную диагностику? Да — с сырыми буферами; сначала закройте официальную утилиту. Нет — только имеющиеся данные мониторинга. Проверьте отчёт перед отправкой.",
             "Зібрати повну діагностику? Так — із сирими буферами; спочатку закрийте офіційну утиліту. Ні — лише наявні дані моніторингу. Перевірте звіт перед надсиланням."),
        ["Find paired Bluetooth devices"] = ("Найти устройства Bluetooth", "Знайти пристрої Bluetooth"),
        ["Read selected battery"] = ("Прочитать заряд", "Зчитати заряд"),
        ["Use this mouse in tray when 2.4 GHz receiver is absent (this session)"] =
            ("Показывать эту мышь при отсутствии USB (только в этой сессии)",
             "Показувати цю мишу за відсутності USB (лише в цій сесії)"),
        ["Manual check of already paired Bluetooth LE and Classic mice."] =
            ("Проверка уже сопряжённых мышей Bluetooth LE и Classic.",
             "Перевірка вже спарених мишей Bluetooth LE та Classic."),
        ["No pairing or GATT writes. Automatic reads require opt-in."] =
            ("Без сопряжения и записи GATT. Автоопрос — только с разрешения.",
             "Без спарювання та запису GATT. Автоопитування — лише з дозволу."),
        ["Choose Find to list already paired devices."] =
            ("Нажмите «Найти», чтобы показать сопряжённые устройства.",
             "Натисніть «Знайти», щоб показати спарені пристрої."),
        ["Checking paired Bluetooth LE and Classic devices..."] =
            ("Поиск сопряжённых устройств Bluetooth LE и Classic...", "Пошук спарених пристроїв Bluetooth LE та Classic..."),
        ["No matching devices. Enable Show all and search again."] =
            ("Устройства не найдены. Включите «Показать все» и повторите поиск.",
             "Пристроїв не знайдено. Увімкніть «Показати всі» й повторіть пошук."),
        ["Select your mouse and click Read selected battery."] =
            ("Выберите мышь и нажмите «Прочитать заряд».",
             "Виберіть мишу й натисніть «Зчитати заряд»."),
        ["Bluetooth lookup timed out."] = ("Время поиска Bluetooth истекло.", "Час пошуку Bluetooth вичерпано."),
        ["Wake the mouse and try again."] = ("Разбудите мышь и повторите.", "Розбудіть мишу та повторіть."),
        ["Bluetooth lookup unavailable: {0}"] = ("Поиск Bluetooth недоступен: {0}", "Пошук Bluetooth недоступний: {0}"),
        ["Reading selected mouse's GATT Battery Service..."] =
            ("Чтение заряда GATT выбранной мыши...", "Зчитування заряду GATT вибраної миші..."),
        ["No battery percentage inferred."] = ("Процент заряда неизвестен.", "Відсоток заряду невідомий."),
        ["Bluetooth Battery Service read timed out. Try waking the mouse."] =
            ("Превышено время чтения батареи Bluetooth. Разбудите мышь.",
             "Перевищено час зчитування батареї Bluetooth. Розбудіть мишу."),
        ["Unable to read this paired mouse's Battery Service."] =
            ("Не удалось прочитать батарею сопряжённой мыши.",
             "Не вдалося зчитати батарею спареної миші."),
        ["Bluetooth tray fallback is enabled for this session."] =
            ("Мониторинг Bluetooth включён на время этой сессии.",
             "Моніторинг Bluetooth увімкнено на час цієї сесії."),
        ["It is used only when the 2.4 GHz receiver is absent."] =
            ("Используется только при отсутствии приёмника 2,4 ГГц.",
             "Використовується лише за відсутності приймача 2,4 ГГц."),
        ["Windows clipboard is unavailable."] =
            ("Буфер обмена Windows недоступен.", "Буфер обміну Windows недоступний."),
        ["Bluetooth fallback: {0}% (fresh GATT)"] =
            ("Bluetooth: {0}% (свеже GATT)", "Bluetooth: {0}% (свіже GATT)"),
        ["Bluetooth fallback: unavailable ({0} failed; last good {1})"] =
            ("Bluetooth: недоступен ({0} ошибок; последнее чтение {1})",
             "Bluetooth: недоступний ({0} помилок; останнє читання {1})")
    };

    public static string Language { get; private set; } = "en";

    /// <summary>Reject unknown codes without changing previous settings.</summary>
    public static string Normalize(string? code) => code is "ru" or "uk" ? code : "en";

    public static void SetLanguage(string? code) => Language = Normalize(code);

    public static string Get(string english)
    {
        if (Language == "en" && english.StartsWith("Tray color ", StringComparison.Ordinal))
        {
            string color = english["Tray color ".Length..];
            if (color == "inherit") return "Global color";
            if (color.Length > 0) return char.ToUpperInvariant(color[0]) + color[1..];
        }
        if (!Messages.TryGetValue(english, out var translated)) return english;
        return Language switch
        {
            "ru" => translated.Ru,
            "uk" => translated.Uk,
            _ => english
        };
    }

    public static string Format(string english, params object[] values)
        => string.Format(System.Globalization.CultureInfo.InvariantCulture,
            Get(english), values);
}
