#import <Cocoa/Cocoa.h>
#import <CoreBluetooth/CoreBluetooth.h>
#import <IOKit/hid/IOHIDManager.h>
#import <IOKit/hid/IOHIDKeys.h>

typedef NS_ENUM(NSInteger, BatteryState) {
    BatteryAbsent = 0, BatteryUnknown = 1, BatteryValid = 2
};

typedef struct {
    BatteryState state;
    NSInteger percent;
    NSInteger collections;
} BatteryReading;

/// Accept only the documented F7/05 telemetry response, not arbitrary bytes.
static NSInteger ParseBattery(const uint8_t *report, CFIndex length) {
    if (length >= 4 && report[0] == 5 && report[1] == 0 &&
        report[2] == 0 && report[3] >= 1 && report[3] <= 100) {
        return report[3];
    }
    if (length >= 3 && report[0] == 0 && report[1] == 0 &&
        report[2] >= 1 && report[2] <= 100) {
        return report[2];
    }
    return -1;
}

static BOOL MatchesVendorCollection(IOHIDDeviceRef device) {
    CFTypeRef page = IOHIDDeviceGetProperty(device, CFSTR(kIOHIDPrimaryUsagePageKey));
    CFTypeRef usage = IOHIDDeviceGetProperty(device, CFSTR(kIOHIDPrimaryUsageKey));
    if (!page || !usage ||
        CFGetTypeID(page) != CFNumberGetTypeID() ||
        CFGetTypeID(usage) != CFNumberGetTypeID()) return NO;
    int p = 0, u = 0;
    CFNumberGetValue(page, kCFNumberIntType, &p);
    CFNumberGetValue(usage, kCFNumberIntType, &u);
    return p == 0xffff && u == 2;
}

static NSInteger ReadFeature(IOHIDDeviceRef device) {
    if (IOHIDDeviceOpen(device, kIOHIDOptionsTypeNone) != kIOReturnSuccess)
        return -1;
    NSInteger percent = -1;
    for (int count = 65; count <= 67; count += 2) {
        uint8_t request[67] = {0};
        request[1] = 0xf7;  // Whitelisted telemetry request only.
        IOReturn write = IOHIDDeviceSetReport(device, kIOHIDReportTypeFeature,
                                               0, request, count);
        if (write != kIOReturnSuccess) continue;
        [NSThread sleepForTimeInterval:0.03];
        uint8_t reply[67] = {0};
        reply[0] = 5;
        CFIndex length = count;
        IOReturn result = IOHIDDeviceGetReport(device, kIOHIDReportTypeFeature,
                                                5, reply, &length);
        if (result == kIOReturnSuccess) {
            percent = ParseBattery(reply, length);
            if (percent >= 0) break;
        }
    }
    IOHIDDeviceClose(device, kIOHIDOptionsTypeNone);
    return percent;
}

/// The only USB query is the original, read-only-in-purpose F7/05 protocol.
static BatteryReading ReadReceiver(void) {
    BatteryReading reading = {BatteryUnknown, -1, 0};
    IOHIDManagerRef manager = IOHIDManagerCreate(kCFAllocatorDefault, 0);
    if (!manager) return reading;
    NSDictionary *matching = @{
        @kIOHIDVendorIDKey: @0x3151,
        @kIOHIDProductIDKey: @0x5007
    };
    IOHIDManagerSetDeviceMatching(manager, (__bridge CFDictionaryRef)matching);
    if (IOHIDManagerOpen(manager, 0) != kIOReturnSuccess) {
        CFRelease(manager);
        return reading;
    }
    CFSetRef devices = IOHIDManagerCopyDevices(manager);
    if (devices) {
        CFIndex count = CFSetGetCount(devices);
        const void **list = calloc((size_t)(count > 0 ? count : 1), sizeof(void *));
        if (list) {
            CFSetGetValues(devices, list);
            reading.state = BatteryAbsent;
            for (CFIndex i = 0; i < count; i++) {
                IOHIDDeviceRef device = (IOHIDDeviceRef)list[i];
                if (!MatchesVendorCollection(device)) continue;
                reading.collections++;
                reading.state = BatteryUnknown;
                NSInteger percent = ReadFeature(device);
                if (percent >= 0) {
                    reading.state = BatteryValid;
                    reading.percent = percent;
                    break;
                }
            }
            free(list);
        }
        CFRelease(devices);
    } else {
        reading.state = BatteryAbsent;
    }
    IOHIDManagerClose(manager, 0);
    CFRelease(manager);
    return reading;
}

@interface LegacyTray : NSObject <NSApplicationDelegate, CBCentralManagerDelegate,
                                   CBPeripheralDelegate>
@property(nonatomic, strong) NSStatusItem *tray;
@property(nonatomic, strong) NSMenuItem *detail;
@property(nonatomic, strong) NSTimer *timer;
@property(nonatomic, strong) CBCentralManager *central;
@property(nonatomic, strong) CBPeripheral *selectedPeripheral;
@property(nonatomic, strong) NSArray<CBPeripheral *> *connectedMice;
@property(nonatomic, assign) BatteryReading latest;
@property(nonatomic, assign) BOOL polling;
@property(nonatomic, assign) BOOL everConnected;
@property(nonatomic, assign) BOOL disconnectSent;
@property(nonatomic, assign) NSInteger absentCount;
@property(nonatomic, assign) NSUInteger alerted;
@property(nonatomic, assign) BOOL bluetoothRequested;
@property(nonatomic, assign) NSUInteger bluetoothRequestGeneration;
@property(nonatomic, assign) NSUInteger bluetoothAttempt;
@end

@implementation LegacyTray

- (NSString *)word:(NSString *)english ru:(NSString *)russian uk:(NSString *)ukrainian {
    NSString *language = [[NSUserDefaults standardUserDefaults] stringForKey:@"LegacyLanguage"];
    if ([language isEqualToString:@"ru"]) return russian;
    if ([language isEqualToString:@"uk"]) return ukrainian;
    return english;
}

- (BOOL)setting:(NSString *)key {
    return [[NSUserDefaults standardUserDefaults] boolForKey:key];
}

- (NSMenuItem *)item:(NSMenu *)menu title:(NSString *)title action:(SEL)action {
    NSMenuItem *item = [menu addItemWithTitle:title action:action keyEquivalent:@""];
    item.target = self;
    return item;
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    [NSApp setActivationPolicy:NSApplicationActivationPolicyAccessory];
    self.tray = [[NSStatusBar systemStatusBar] statusItemWithLength:NSVariableStatusItemLength];
    self.tray.button.title = @"AJAZZ ?";
    self.latest = (BatteryReading){BatteryUnknown, -1, 0};
    [self buildMenu];
    [self scheduleTimer];
    [self refresh:nil];
}

- (void)buildMenu {
    NSMenu *menu = [[NSMenu alloc] initWithTitle:@"AJAZZ High Sierra"];
    self.detail = [self item:menu title:@"Checking USB receiver…" action:NULL];
    self.detail.enabled = NO;
    [menu addItem:[NSMenuItem separatorItem]];
    [self item:menu title:[self word:@"Refresh now" ru:@"Обновить" uk:@"Оновити"]
                   action:@selector(refresh:)];
    [self item:menu title:[self word:@"Check connected Bluetooth battery…"
                                    ru:@"Проверить Bluetooth…" uk:@"Перевірити Bluetooth…"]
                   action:@selector(checkBluetooth:)];
    [self item:menu title:[self word:@"Copy diagnostics" ru:@"Копировать диагностику"
                                    uk:@"Копіювати діагностику"]
                   action:@selector(copyDiagnostics:)];
    [menu addItem:[NSMenuItem separatorItem]];

    NSMenu *settings = [[NSMenu alloc] initWithTitle:@"Settings"];
    NSMenuItem *low = [self item:settings
        title:[self word:@"Low-battery notifications" ru:@"Уведомления о заряде"
                         uk:@"Сповіщення про заряд"]
        action:@selector(toggleLow:)];
    low.state = [self setting:@"LegacyNotifyLow"] ? NSControlStateValueOn : NSControlStateValueOff;
    NSMenuItem *disconnect = [self item:settings
        title:[self word:@"Receiver disconnect notifications" ru:@"Отключение приёмника"
                         uk:@"Відключення приймача"]
        action:@selector(toggleDisconnect:)];
    disconnect.state = [self setting:@"LegacyNotifyDisconnect"] ? NSControlStateValueOn : NSControlStateValueOff;

    NSMenu *thresholds = [[NSMenu alloc] initWithTitle:@"Thresholds"];
    NSUInteger mask = [self thresholdMask];
    for (NSInteger percent = 50; percent >= 10; percent = percent == 50 ? 25 : 10) {
        NSMenuItem *entry = [self item:thresholds
             title:[NSString stringWithFormat:@"< %ld%%", (long)percent]
             action:@selector(toggleThreshold:)];
        entry.tag = percent;
        NSUInteger bit = percent == 50 ? 1 : (percent == 25 ? 2 : 4);
        entry.state = (mask & bit) ? NSControlStateValueOn : NSControlStateValueOff;
        if (percent == 10) break;
    }
    NSMenuItem *thresholdItem = [settings addItemWithTitle:
        [self word:@"Alert thresholds" ru:@"Пороги уведомлений" uk:@"Пороги сповіщень"]
        action:NULL keyEquivalent:@""];
    thresholdItem.submenu = thresholds;

    NSMenu *intervals = [[NSMenu alloc] initWithTitle:@"Refresh interval"];
    for (NSNumber *n in @[@15, @30, @60, @120]) {
        NSMenuItem *entry = [self item:intervals
            title:[NSString stringWithFormat:@"%@ s", n]
            action:@selector(setInterval:)];
        entry.tag = n.integerValue;
        entry.state = [self interval] == n.integerValue ?
            NSControlStateValueOn : NSControlStateValueOff;
    }
    NSMenuItem *intervalItem = [settings addItemWithTitle:
        [self word:@"Refresh interval" ru:@"Интервал опроса" uk:@"Інтервал опитування"]
        action:NULL keyEquivalent:@""];
    intervalItem.submenu = intervals;

    NSMenu *languages = [[NSMenu alloc] initWithTitle:@"Language"];
    for (NSString *language in @[@"en", @"ru", @"uk"]) {
        NSString *label = @{@"en":@"English", @"ru":@"Русский",
                            @"uk":@"Українська"}[language];
        NSMenuItem *entry = [self item:languages title:label action:@selector(setLanguage:)];
        entry.representedObject = language;
        NSString *selected = [[NSUserDefaults standardUserDefaults]
                              stringForKey:@"LegacyLanguage"] ?: @"en";
        entry.state = [selected isEqualToString:language] ?
            NSControlStateValueOn : NSControlStateValueOff;
    }
    NSMenuItem *languageItem = [settings addItemWithTitle:
        [self word:@"Language" ru:@"Язык" uk:@"Мова"] action:NULL keyEquivalent:@""];
    languageItem.submenu = languages;
    NSMenuItem *settingsItem = [menu addItemWithTitle:
        [self word:@"Settings" ru:@"Настройки" uk:@"Налаштування"]
        action:NULL keyEquivalent:@""];
    settingsItem.submenu = settings;
    [menu addItem:[NSMenuItem separatorItem]];
    [self item:menu title:[self word:@"Quit" ru:@"Выход" uk:@"Вийти"]
                   action:@selector(quit:)];
    self.tray.menu = menu;
    [self display:self.latest];
}

- (NSInteger)interval {
    NSInteger value = [[NSUserDefaults standardUserDefaults]
                       integerForKey:@"LegacyPollSeconds"];
    return value == 15 || value == 60 || value == 120 ? value : 30;
}

- (NSUInteger)thresholdMask {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    if (![defaults objectForKey:@"LegacyThresholdMask"]) return 7;
    return (NSUInteger)[defaults integerForKey:@"LegacyThresholdMask"] & 7;
}

- (void)scheduleTimer {
    [self.timer invalidate];
    self.timer = [NSTimer scheduledTimerWithTimeInterval:(NSTimeInterval)[self interval]
        target:self selector:@selector(refresh:) userInfo:nil repeats:YES];
}

- (void)display:(BatteryReading)reading {
    if (reading.state == BatteryValid) {
        self.tray.button.title = [NSString stringWithFormat:@"🔋%ld%%",
                                 (long)reading.percent];
        self.detail.title = [NSString stringWithFormat:@"AJAZZ APEX: %ld%%",
                             (long)reading.percent];
    } else if (reading.state == BatteryAbsent) {
        self.tray.button.title = @"AJAZZ —";
        self.detail.title = [self word:@"Compatible receiver not found"
                                       ru:@"Совместимый приёмник не найден"
                                       uk:@"Сумісний приймач не знайдено"];
    } else {
        self.tray.button.title = @"AJAZZ ?";
        self.detail.title = [self word:@"Receiver present; battery unknown"
                                       ru:@"Приёмник найден, заряд неизвестен"
                                       uk:@"Приймач знайдено, заряд невідомий"];
    }
}

- (void)notify:(NSString *)title message:(NSString *)message {
    NSUserNotification *note = [[NSUserNotification alloc] init];
    note.title = title;
    note.informativeText = message;
    [[NSUserNotificationCenter defaultUserNotificationCenter]
        deliverNotification:note];
}

- (void)evaluateAlerts:(BatteryReading)reading {
    if (reading.state == BatteryUnknown) {
        self.absentCount = 0; // Sleeping mouse is not a disconnected receiver.
        return;
    }
    if (reading.state == BatteryAbsent) {
        self.absentCount++;
        if (self.everConnected && self.absentCount >= 2 &&
            !self.disconnectSent && [self setting:@"LegacyNotifyDisconnect"]) {
            self.disconnectSent = YES;
            [self notify:@"AJAZZ APEX" message:
                [self word:@"USB receiver disconnected" ru:@"Приёмник отключён"
                              uk:@"Приймач відключено"]];
        }
        return;
    }
    self.everConnected = YES;
    self.absentCount = 0;
    self.disconnectSent = NO;
    NSUInteger mask = [self thresholdMask];
    for (NSInteger threshold = 50; threshold >= 10;
         threshold = threshold == 50 ? 25 : 10) {
        NSUInteger bit = threshold == 50 ? 1 : (threshold == 25 ? 2 : 4);
        if (reading.percent >= threshold + 5) self.alerted &= ~bit;
        if (threshold == 10) break;
    }
    NSUInteger newlyCrossed = 0;
    for (NSInteger threshold = 50; threshold >= 10;
         threshold = threshold == 50 ? 25 : 10) {
        NSUInteger bit = threshold == 50 ? 1 : (threshold == 25 ? 2 : 4);
        if (reading.percent < threshold && !(self.alerted & bit) && (mask & bit))
            newlyCrossed = bit;
        if (reading.percent < threshold) self.alerted |= bit;
        if (threshold == 10) break;
    }
    if (newlyCrossed && [self setting:@"LegacyNotifyLow"]) {
        [self notify:@"AJAZZ APEX" message:
            [NSString stringWithFormat:
             [self word:@"Low battery: %ld%%" ru:@"Низкий заряд: %ld%%"
                         uk:@"Низький заряд: %ld%%"], (long)reading.percent]];
    }
}

- (void)refresh:(id)sender {
    if (self.polling) return;
    self.polling = YES;
    __weak LegacyTray *weakSelf = self;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        @autoreleasepool {
            BatteryReading reading = ReadReceiver();
            dispatch_async(dispatch_get_main_queue(), ^{
                LegacyTray *owner = weakSelf;
                if (!owner) return;
                owner.latest = reading;
                owner.polling = NO;
                [owner display:reading];
                [owner evaluateAlerts:reading];
            });
        }
    });
}

- (void)toggleLow:(id)sender {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    [defaults setBool:![self setting:@"LegacyNotifyLow"] forKey:@"LegacyNotifyLow"];
    [self buildMenu];
}

- (void)toggleDisconnect:(id)sender {
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    [defaults setBool:![self setting:@"LegacyNotifyDisconnect"]
             forKey:@"LegacyNotifyDisconnect"];
    [self buildMenu];
}

- (void)toggleThreshold:(NSMenuItem *)sender {
    NSUInteger bit = sender.tag == 50 ? 1 : (sender.tag == 25 ? 2 : 4);
    [[NSUserDefaults standardUserDefaults] setInteger:(NSInteger)([self thresholdMask] ^ bit)
                                                forKey:@"LegacyThresholdMask"];
    [self buildMenu];
}

- (void)setInterval:(NSMenuItem *)sender {
    [[NSUserDefaults standardUserDefaults] setInteger:sender.tag
                                                forKey:@"LegacyPollSeconds"];
    [self scheduleTimer];
    [self buildMenu];
}

- (void)setLanguage:(NSMenuItem *)sender {
    [[NSUserDefaults standardUserDefaults] setObject:sender.representedObject
                                              forKey:@"LegacyLanguage"];
    [self buildMenu];
}

- (NSString *)diagnostics {
    NSString *state = self.latest.state == BatteryValid ? @"valid" :
        (self.latest.state == BatteryAbsent ? @"not connected" : @"unknown");
    return [NSString stringWithFormat:
        @"AJAZZ Battery Tray High Sierra Edition\n"
         @"OS: %@\nVID:PID: 3151:5007\nUsage: FFFF:0002\n"
         @"Battery state: %@\nMatching HID collections: %ld\n"
         @"Firmware and device serial numbers were not queried.",
         [[NSProcessInfo processInfo] operatingSystemVersionString],
         state, (long)self.latest.collections];
}

- (void)copyDiagnostics:(id)sender {
    NSPasteboard *board = [NSPasteboard generalPasteboard];
    [board clearContents];
    [board setString:[self diagnostics] forType:NSPasteboardTypeString];
}

- (void)message:(NSString *)text {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = @"AJAZZ Battery Tray — High Sierra";
    alert.informativeText = text;
    [NSApp activateIgnoringOtherApps:YES];
    [alert runModal];
}

- (void)checkBluetooth:(id)sender {
    if (self.selectedPeripheral || self.bluetoothRequested) return;
    self.bluetoothRequested = YES;
    NSUInteger generation = ++self.bluetoothRequestGeneration;
    if (!self.central) {
        self.central = [[CBCentralManager alloc] initWithDelegate:self queue:nil];
    } else {
        [self centralManagerDidUpdateState:self.central];
    }
    // The first radio state callback may never arrive; keep manual retry usable.
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 10 * NSEC_PER_SEC),
                   dispatch_get_main_queue(), ^{
        if (!self.bluetoothRequested ||
            generation != self.bluetoothRequestGeneration) return;
        self.bluetoothRequested = NO;
        [self message:@"Bluetooth initialization timed out; try again."];
    });
}

- (void)centralManagerDidUpdateState:(CBCentralManager *)central {
    // Unsolicited radio state changes must not open a modal window.
    if (!self.bluetoothRequested) return;
    if (central.state == CBManagerStateUnknown ||
        central.state == CBManagerStateResetting) return;
    self.bluetoothRequested = NO;
    if (central.state != CBManagerStatePoweredOn) {
        [self message:[self word:@"Bluetooth is off or unavailable."
                                 ru:@"Bluetooth выключен или недоступен."
                                 uk:@"Bluetooth вимкнений або недоступний."]];
        return;
    }
    CBUUID *service = [CBUUID UUIDWithString:@"180F"];
    NSArray<CBPeripheral *> *connected =
        [central retrieveConnectedPeripheralsWithServices:@[service]];
    NSMutableArray<CBPeripheral *> *matching = [NSMutableArray array];
    for (CBPeripheral *device in connected) {
        NSString *name = device.name.uppercaseString ?: @"";
        if ([name containsString:@"AJAZZ"] || [name containsString:@"AJ159"] ||
            [name containsString:@"AJ179"]) [matching addObject:device];
    }
    self.connectedMice = matching;
    if (!matching.count) {
        [self message:@"No connected AJAZZ BLE mouse exposes Battery Service (180F)."];
        return;
    }
    NSPopUpButton *choice = [[NSPopUpButton alloc] initWithFrame:
        NSMakeRect(0, 0, 340, 26) pullsDown:NO];
    for (CBPeripheral *device in matching) {
        [choice addItemWithTitle:device.name ?: @"AJAZZ APEX"];
    }
    NSAlert *dialog = [[NSAlert alloc] init];
    dialog.messageText = @"Choose connected AJAZZ mouse";
    dialog.informativeText = @"Manual GATT 180F / 2A19 read. No scanning or pairing.";
    dialog.accessoryView = choice;
    [dialog addButtonWithTitle:@"Read battery"];
    [dialog addButtonWithTitle:@"Cancel"];
    [NSApp activateIgnoringOtherApps:YES];
    if ([dialog runModal] != NSAlertFirstButtonReturn) return;
    NSInteger index = choice.indexOfSelectedItem;
    if (index < 0 || index >= (NSInteger)matching.count) return;
    self.selectedPeripheral = matching[(NSUInteger)index];
    self.bluetoothAttempt++;
    NSUInteger attempt = self.bluetoothAttempt;
    self.selectedPeripheral.delegate = self;
    [central connectPeripheral:self.selectedPeripheral options:nil];
    CBPeripheral *pending = self.selectedPeripheral;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 10 * NSEC_PER_SEC),
                   dispatch_get_main_queue(), ^{
        // A previous attempt must not terminate a newer read of the same mouse.
        if (self.selectedPeripheral == pending && self.bluetoothAttempt == attempt) {
            [self finishBluetooth:@"Bluetooth Battery Service timed out."];
        }
    });
}

- (void)centralManager:(CBCentralManager *)central didConnectPeripheral:(CBPeripheral *)device {
    if (device == self.selectedPeripheral)
        [device discoverServices:@[[CBUUID UUIDWithString:@"180F"]]];
}

- (void)centralManager:(CBCentralManager *)central didFailToConnectPeripheral:
    (CBPeripheral *)device error:(NSError *)error {
    if (device == self.selectedPeripheral)
        [self finishBluetooth:@"Failed to read connected Bluetooth mouse."];
}

- (void)peripheral:(CBPeripheral *)device didDiscoverServices:(NSError *)error {
    if (device != self.selectedPeripheral) return;
    if (error) {
        [self finishBluetooth:@"Bluetooth service discovery failed."];
        return;
    }
    for (CBService *service in device.services) {
        if ([service.UUID isEqual:[CBUUID UUIDWithString:@"180F"]]) {
            [device discoverCharacteristics:@[[CBUUID UUIDWithString:@"2A19"]]
                                 forService:service];
            return;
        }
    }
    [self finishBluetooth:@"Battery Service (180F) is unavailable."];
}

- (void)peripheral:(CBPeripheral *)device didDiscoverCharacteristicsForService:
    (CBService *)service error:(NSError *)error {
    if (device != self.selectedPeripheral) return;
    if (error) {
        [self finishBluetooth:@"Bluetooth characteristic discovery failed."];
        return;
    }
    for (CBCharacteristic *characteristic in service.characteristics) {
        if ([characteristic.UUID isEqual:[CBUUID UUIDWithString:@"2A19"]]) {
            [device readValueForCharacteristic:characteristic];
            return;
        }
    }
    [self finishBluetooth:@"Battery Level (2A19) is unavailable."];
}

- (void)peripheral:(CBPeripheral *)device didUpdateValueForCharacteristic:
    (CBCharacteristic *)characteristic error:(NSError *)error {
    if (device != self.selectedPeripheral) return;
    NSData *value = characteristic.value;
    if (!error && value.length == 1 && ((const uint8_t *)value.bytes)[0] <= 100) {
        [self finishBluetooth:[NSString stringWithFormat:
            @"Bluetooth battery: %d%%", ((const uint8_t *)value.bytes)[0]]];
    } else {
        [self finishBluetooth:@"No valid Bluetooth Battery Level returned."];
    }
}

- (void)centralManager:(CBCentralManager *)central
    didDisconnectPeripheral:(CBPeripheral *)device error:(NSError *)error {
    if (device == self.selectedPeripheral) {
        [self finishBluetooth:@"Bluetooth mouse disconnected before the read completed."];
    }
}

- (void)finishBluetooth:(NSString *)message {
    if (!self.selectedPeripheral) return;
    self.selectedPeripheral.delegate = nil;
    [self.central cancelPeripheralConnection:self.selectedPeripheral];
    self.selectedPeripheral = nil;
    [self message:message];
}

- (void)quit:(id)sender { [NSApp terminate:nil]; }
@end

int main(void) {
    @autoreleasepool {
        NSArray<NSString *> *arguments = [[NSProcessInfo processInfo] arguments];
        if ([arguments containsObject:@"--help"] || [arguments containsObject:@"-h"]) {
            puts("Usage: AJAZZBatteryTrayHighSierra [--help|--self-test|--diagnose]");
            return 0;
        }
        if ([arguments containsObject:@"--self-test"]) {
            uint8_t first[] = {5, 0, 0, 1};
            uint8_t full[] = {5, 0, 0, 100};
            uint8_t stripped[] = {0, 0, 25};
            uint8_t zero[] = {5, 0, 0, 0};
            uint8_t excess[] = {5, 0, 0, 101};
            uint8_t wrongID[] = {6, 0, 0, 83};
            uint8_t malformed[] = {5, 1, 0, 83};
            uint8_t shortFrame[] = {5, 0};
            BOOL pass = ParseBattery(first, 4) == 1 &&
                ParseBattery(full, 4) == 100 &&
                ParseBattery(stripped, 3) == 25 &&
                ParseBattery(zero, 4) == -1 &&
                ParseBattery(excess, 4) == -1 &&
                ParseBattery(wrongID, 4) == -1 &&
                ParseBattery(malformed, 4) == -1 &&
                ParseBattery(shortFrame, 2) == -1;
            puts(pass ? "PASS: 8 HID parser cases" : "FAIL: HID parser regression");
            return pass ? 0 : 1;
        }
        if ([arguments containsObject:@"--diagnose"]) {
            BatteryReading reading = ReadReceiver();
            printf("VID:PID 3151:5007 | matching collections %ld | ",
                   (long)reading.collections);
            if (reading.state == BatteryValid)
                printf("PASS: battery %ld%%\n", (long)reading.percent);
            else if (reading.state == BatteryAbsent)
                puts("UNKNOWN: compatible receiver not found");
            else
                puts("UNKNOWN: no verified battery response");
            return reading.state == BatteryValid ? 0 : 2;
        }
        NSApplication *app = [NSApplication sharedApplication];
        LegacyTray *delegate = [[LegacyTray alloc] init];
        app.delegate = delegate;
        [app run];
    }
    return 0;
}
