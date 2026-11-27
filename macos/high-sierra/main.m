#import "TrayAppearance.h"
#import <Cocoa/Cocoa.h>
#import "diagnostic_runner.h"
#import "../AjazzBatteryReport.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>
#import <CoreBluetooth/CoreBluetooth.h>
#import <IOKit/hid/IOHIDManager.h>
#import <IOKit/hid/IOHIDKeys.h>

typedef NS_ENUM(NSInteger, BatteryState) {
    BatteryAbsent = 0,
    BatteryUnknown = 1,
    BatteryValid = 2,
    BatteryAccessError = 3,
    BatteryUnexpectedUsage = 4,
    BatteryTimedOut = 5,
    BatteryChecking = 6,
    BatteryCancelled = 7
};

typedef struct {
    BatteryState state;
    NSInteger percent;
    NSInteger collections;
} BatteryReading;

/// Historical session observation, not an identity-bound receiver cache.
static NSDate *SessionVerifiedAt(NSDate *previous, BatteryReading reading, NSDate *now) {
    if (reading.state == BatteryValid && reading.percent >= 1 && reading.percent <= 100)
        return now;
    return reading.state == BatteryAbsent ? nil : previous;
}

/// Project the last reading without mutating history, alerts or receiver state.
static BatteryReading PresentationReading(BatteryReading reading, NSDate *stamp, NSDate *now) {
    if (reading.state == BatteryValid && (!stamp || reading.percent < 1 ||
        reading.percent > 100 || !AjazzSampleAgeIsCurrent([now timeIntervalSinceDate:stamp]))) {
        reading.state = BatteryUnknown;
        reading.percent = -1;
    }
    return reading;
}

/// Accept only the documented F7/05 telemetry response, not arbitrary bytes.
static NSInteger ParseBattery(const uint8_t *report, CFIndex length) {
    return length > 0 ? AjazzBatteryPercent(report, (size_t)length) : -1;
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

static NSInteger ReadFeature(IOHIDDeviceRef device, BOOL *accessFailed) {
    *accessFailed = NO;
    if (IOHIDDeviceOpen(device, kIOHIDOptionsTypeNone) != kIOReturnSuccess) {
        *accessFailed = YES;
        return -1;
    }
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
        if (result == kIOReturnSuccess && length >= 3 && length <= count) {
            percent = ParseBattery(reply, length);
            if (percent >= 0) break;
        }
    }
    IOHIDDeviceClose(device, kIOHIDOptionsTypeNone);
    return percent;
}

/// The only USB query is the original, read-only-in-purpose F7/05 protocol.
static BatteryReading ReadReceiverUnlocked(void) {
    BatteryReading reading = {BatteryAccessError, -1, 0};
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
            reading.state = count ? BatteryUnexpectedUsage : BatteryAbsent;
            BOOL anyOpened = NO;
            for (CFIndex i = 0; i < count; i++) {
                IOHIDDeviceRef device = (IOHIDDeviceRef)list[i];
                if (!MatchesVendorCollection(device)) continue;
                reading.collections++;
                reading.state = BatteryUnknown;
                BOOL accessFailed = NO;
                NSInteger percent = ReadFeature(device, &accessFailed);
                if (!accessFailed) anyOpened = YES;
                if (percent >= 0) {
                    reading.state = BatteryValid;
                    reading.percent = percent;
                    break;
                }
            }
            if (reading.state == BatteryUnknown && !anyOpened)
                reading.state = BatteryAccessError;
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


/// A busy or unsafe gate is unknown presence, never confirmed removal.
static BatteryReading ReadReceiver(void) {
    int lease = AjazzAcquireIoLease();
    if (lease < 0) return (BatteryReading){BatteryAccessError, -1, 0};
    BatteryReading result = ReadReceiverUnlocked();
    AjazzReleaseIoLease(lease);
    return result;
}

/// Local fixed-size IPC for a same-binary worker; no raw HID or identity.
static BOOL DecodeRoutineReply(NSData *data, BatteryReading *reading) {
    int32_t fields[3];
    if (data.length != sizeof(fields)) return NO;
    [data getBytes:fields length:sizeof(fields)];
    int32_t state = fields[0], percent = fields[1], count = fields[2];
    if (state < BatteryAbsent || state > BatteryUnexpectedUsage ||
        count < 0 || count > 4096) return NO;
    if (state == BatteryValid) {
        if (percent < 1 || percent > 100 || count == 0) return NO;
    } else if (percent != -1) return NO;
    if (state == BatteryAbsent && count != 0) return NO;
    *reading = (BatteryReading){state, percent, count};
    return YES;
}

static int RoutineChild(const char *mode) {
    signal(SIGALRM, SIG_DFL);
    alarm(12);
    if (!strcmp(mode, "--internal-routine-hang")) {
        sleep(30);
        return 1;
    }
    BatteryReading reading = !strcmp(mode, "--internal-routine-sample")
        ? (BatteryReading){BatteryUnknown, -1, 1} : ReadReceiver();
    int32_t fields[] = {(int32_t)reading.state, (int32_t)reading.percent,
                        (int32_t)reading.collections};
    int result = fwrite(fields, sizeof(fields), 1, stdout) == 1 ? 0 : 1;
    alarm(0);
    return result;
}

static NSLock *RoutineGate(void) {
    static NSLock *gate;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ gate = [[NSLock alloc] init]; });
    return gate;
}

/// Only the supervisor signals its child; the UI sets a thread-safe flag.
@interface LegacyPollCancellation : NSObject
@property(atomic, assign, getter=isCancelled) BOOL cancelled;
@end
@implementation LegacyPollCancellation
@end

static void StopRoutineChild(NSTask *child) {
    if (child.running) kill(child.processIdentifier, SIGKILL);
    [child waitUntilExit];
}

/// Keep the in-process gate until NSTask confirms child exit.
static BatteryReading RunRoutineUnlocked(NSString *mode, NSTimeInterval timeout,
                                         LegacyPollCancellation *token) {
    BatteryReading result = {BatteryAccessError, -1, 0};
    if (token.isCancelled) return (BatteryReading){BatteryCancelled, -1, 0};
    NSString *path = [[NSBundle mainBundle] executablePath];
    if (!path.length) return result;
    NSTask *child = [[NSTask alloc] init];
    NSPipe *pipe = [NSPipe pipe];
    dispatch_semaphore_t done = dispatch_semaphore_create(0);
    child.launchPath = path;
    child.arguments = @[mode];
    child.standardOutput = pipe;
    child.standardError = [NSFileHandle fileHandleWithNullDevice];
    child.terminationHandler = ^(NSTask *task) {
        (void)task;
        dispatch_semaphore_signal(done);
    };
    @try { [child launch]; }
    @catch (NSException *error) { (void)error; return result; }
    // NSTask closes the parent's writing end when given an NSPipe.
    uint64_t deadline = dispatch_time(DISPATCH_TIME_NOW,
        (int64_t)(timeout * NSEC_PER_SEC));
    for (;;) {
        if (token.isCancelled) {
            StopRoutineChild(child);
            return (BatteryReading){BatteryCancelled, -1, 0};
        }
        uint64_t now = dispatch_time(DISPATCH_TIME_NOW, 0);
        if (now >= deadline) {
            StopRoutineChild(child);
            return (BatteryReading){BatteryTimedOut, -1, 0};
        }
        uint64_t next = dispatch_time(DISPATCH_TIME_NOW, 50 * NSEC_PER_MSEC);
        if (dispatch_semaphore_wait(done, MIN(next, deadline)) == 0) break;
    }
    [child waitUntilExit];
    if (token.isCancelled) return (BatteryReading){BatteryCancelled, -1, 0};
    if (child.terminationReason == NSTaskTerminationReasonExit &&
        child.terminationStatus == 0) {
        NSData *data = [pipe.fileHandleForReading readDataToEndOfFile];
        DecodeRoutineReply(data, &result);
    }
    return result;
}

static BatteryReading RunRoutine(NSString *mode, NSTimeInterval timeout,
                                 LegacyPollCancellation *token) {
    if (token.isCancelled) return (BatteryReading){BatteryCancelled, -1, 0};
    NSLock *gate = RoutineGate();
    if (![gate tryLock]) return (BatteryReading){BatteryAccessError, -1, 0};
    @try { return RunRoutineUnlocked(mode, timeout, token); }
    @finally { [gate unlock]; }
}

static int RoutineSelfTest(void) {
    const int32_t samples[][3] = {
        {BatteryValid, 83, 1}, {BatteryAbsent, -1, 0},
        {BatteryUnknown, -1, 1}, {BatteryAccessError, -1, 0},
        {BatteryUnexpectedUsage, -1, 0}
    };
    BatteryReading reading;
    for (size_t i = 0; i < sizeof(samples) / sizeof(samples[0]); i++) {
        NSData *data = [NSData dataWithBytes:samples[i] length:sizeof(samples[i])];
        if (!DecodeRoutineReply(data, &reading) || reading.state != samples[i][0] ||
            reading.percent != samples[i][1] || reading.collections != samples[i][2]) return 1;
    }
    const int32_t invalid[][3] = {
        {BatteryValid, 0, 1}, {BatteryValid, 101, 1},
        {BatteryAbsent, 83, 0}, {BatteryValid, 83, 0},
        {BatteryTimedOut, -1, 0}, {BatteryUnknown, -1, -1}
    };
    for (size_t i = 0; i < sizeof(invalid) / sizeof(invalid[0]); i++) {
        if (DecodeRoutineReply([NSData dataWithBytes:invalid[i]
                length:sizeof(invalid[i])], &reading)) return 1;
    }
    [RoutineGate() lock];
    reading = RunRoutine(@"--internal-routine-sample", 1, nil);
    [RoutineGate() unlock];
    if (reading.state != BatteryAccessError) return 1;
    if (RunRoutine(@"--internal-routine-sample", 8, nil).state != BatteryUnknown ||
        RunRoutine(@"--internal-routine-hang", 1, nil).state != BatteryTimedOut)
        return 1;
    LegacyPollCancellation *before = [[LegacyPollCancellation alloc] init];
    before.cancelled = YES;
    if (RunRoutine(@"--internal-routine-sample", 8, before).state != BatteryCancelled)
        return 1;
    LegacyPollCancellation *during = [[LegacyPollCancellation alloc] init];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 250 * NSEC_PER_MSEC),
                   dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        during.cancelled = YES;
    });
    if (RunRoutine(@"--internal-routine-hang", 4, during).state != BatteryCancelled)
        return 1;
    reading = RunRoutine(@"--internal-routine-sample", 8, nil);
    if (reading.state != BatteryUnknown || reading.percent != -1 ||
        reading.collections != 1) return 1;
    puts("PASS: legacy routine IPC, overlap, timeout, cancellation and recovery (no HID)");
    return 0;
}

/// Emit only the first eight bytes, never a complete vendor HID packet.
static void PrintHIDPrefix(const uint8_t *reply, CFIndex length) {
    CFIndex prefix = length < 8 ? length : 8;
    fputs("05.reply.first_bytes=", stdout);
    for (CFIndex i = 0; i < prefix; i++)
        printf("%s%02x", i ? " " : "", (unsigned int)reply[i]);
    putchar('\n');
}

/// Sends only the existing, approved battery telemetry F7/05 request.
static NSInteger TraceFeature(IOHIDDeviceRef device) {
    for (CFIndex count = 65; count <= 67; count += 2) {
        uint8_t request[67] = {0};
        request[1] = 0xf7;
        printf("STEP: F7.set.length=%ld\n", (long)count);
        IOReturn sent = IOHIDDeviceSetReport(device, kIOHIDReportTypeFeature,
                                             0, request, count);
        printf("F7.set.length=%ld result=0x%08x\n",
               (long)count, (unsigned int)sent);
        if (sent != kIOReturnSuccess) continue;
        [NSThread sleepForTimeInterval:0.03];
        uint8_t reply[67] = {0};
        reply[0] = 5;
        CFIndex actual = count;
        printf("STEP: 05.get.length=%ld\n", (long)count);
        IOReturn got = IOHIDDeviceGetReport(device, kIOHIDReportTypeFeature,
                                            5, reply, &actual);
        printf("05.get.result=0x%08x length=%ld\n",
               (unsigned int)got, (long)actual);
        if (got != kIOReturnSuccess) continue;
        if (actual < 0 || actual > count) {
            puts("05.get.invalid_length");
            continue;
        }
        PrintHIDPrefix(reply, actual);
        printf("F7 policy gate: %s\n", AjazzF7ReplyGateName(reply, (size_t)actual));
        NSInteger percent = ParseBattery(reply, actual);
        if (percent >= 0) return percent;
    }
    return -1;
}

/// Test only the already matched vendor-defined HID collection.
static NSInteger TraceCollections(const void **list, CFIndex count,
                                  NSInteger *matches) {
    for (CFIndex i = 0; i < count; i++) {
        IOHIDDeviceRef device = (IOHIDDeviceRef)list[i];
        if (!MatchesVendorCollection(device)) continue;
        (*matches)++;
        CFTypeRef revision = IOHIDDeviceGetProperty(device, CFSTR("VersionNumber"));
        CFTypeRef feature = IOHIDDeviceGetProperty(device, CFSTR("MaxFeatureReportSize"));
        int rev = -1, size = -1;
        if (revision && CFGetTypeID(revision) == CFNumberGetTypeID())
            CFNumberGetValue(revision, kCFNumberIntType, &rev);
        if (feature && CFGetTypeID(feature) == CFNumberGetTypeID())
            CFNumberGetValue(feature, kCFNumberIntType, &size);
        printf("collection.%ld.revision=%d feature_bytes=%d\n", (long)*matches, rev, size);
        puts("STEP: collection.open");
        IOReturn opened = IOHIDDeviceOpen(device, 0);
        printf("collection.%ld.open=0x%08x\n",
               (long)*matches, (unsigned int)opened);
        if (opened != kIOReturnSuccess) continue;
        NSInteger percent = TraceFeature(device);
        IOHIDDeviceClose(device, 0);
        if (percent >= 0) return percent;
    }
    return -1;
}

/// Explicit diagnostic; outputs only operation status and bounded prefix.
static int TraceReceiverUnlocked(void) {
    puts("AJAZZ High Sierra HID telemetry trace (no serial numbers)");
    puts("VID:PID=3151:5007 expected usage=FFFF:0002");
    IOHIDManagerRef manager = IOHIDManagerCreate(kCFAllocatorDefault, 0);
    if (!manager) return 1;
    NSDictionary *matching = @{
        @kIOHIDVendorIDKey: @0x3151,
        @kIOHIDProductIDKey: @0x5007
    };
    IOHIDManagerSetDeviceMatching(manager, (__bridge CFDictionaryRef)matching);
    puts("STEP: manager.open");
    IOReturn opened = IOHIDManagerOpen(manager, 0);
    printf("manager.open=0x%08x\n", (unsigned int)opened);
    if (opened != kIOReturnSuccess) {
        CFRelease(manager);
        return 2;
    }
    puts("STEP: receiver.enumerate");
    CFSetRef devices = IOHIDManagerCopyDevices(manager);
    CFIndex count = devices ? CFSetGetCount(devices) : 0;
    printf("receiver.hid_count=%ld\n", (long)count);
    const void **list = calloc((size_t)(count > 0 ? count : 1), sizeof(void *));
    BOOL allocated = list != NULL;
    NSInteger matches = 0;
    NSInteger battery = -1;
    if (list && devices && count > 0) {
        CFSetGetValues(devices, list);
        battery = TraceCollections(list, count, &matches);
    }
    printf("matched_vendor_collections=%ld\n", (long)matches);
    free(list);
    if (devices) CFRelease(devices);
    IOHIDManagerClose(manager, 0);
    CFRelease(manager);
    if (!allocated) return 1;
    if (battery < 0) {
        puts("INCONCLUSIVE: no validated battery report");
        return 2;
    }
    printf("PASS: battery=%ld%%\n", (long)battery);
    return 0;
}

static int TraceReceiver(void) {
    int lease = AjazzAcquireIoLease();
    if (lease < 0) {
        puts("INCONCLUSIVE: vendor I/O gate unavailable; no HID request");
        return 2;
    }
    int result = TraceReceiverUnlocked();
    AjazzReleaseIoLease(lease);
    return result;
}

/// Keep only complete non-terminal records from an interrupted capture.
static NSString *IncompleteMenuTrace(NSString *text, NSString *reason) {
    NSMutableArray *lines = [NSMutableArray array];
    NSArray *records = [text componentsSeparatedByString:@"\n"];
    for (NSUInteger i = 0; i + 1 < records.count; i++) {
        NSString *line = records[i];
        if ([line hasPrefix:@"PASS: battery="] || [line hasPrefix:@"Diagnostic exit:"] ||
            [line hasPrefix:@"INCOMPLETE:"]) continue;
        [lines addObject:line];
    }
    return [NSString stringWithFormat:@"INCOMPLETE: %@; no fresh battery claimed\n%@",
            reason, [lines componentsJoinedByString:@"\n"]];
}

/// Nonblocking drain keeps the child pipe moving without unbounded retention.
static BOOL DrainMenuTrace(int fd, NSMutableData *captured, BOOL *truncated) {
    uint8_t buffer[1024];
    for (int i = 0; i < 16; i++) {
        ssize_t count = read(fd, buffer, sizeof(buffer));
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) return errno == EAGAIN || errno == EWOULDBLOCK;
        if (count == 0) return YES;
        NSUInteger remaining = 4096 - captured.length;
        NSUInteger keep = MIN(remaining, (NSUInteger)count);
        if (keep) [captured appendBytes:buffer length:keep];
        if (keep < (NSUInteger)count) *truncated = YES;
    }
    return YES;
}

/// Direct same-binary GUI worker; only this supervisor may stop and reap it.
static NSString *CaptureMenuTrace(BOOL synthetic, LegacyPollCancellation *token,
                                  NSTimeInterval timeout) {
    if (token.isCancelled) return IncompleteMenuTrace(@"", @"cancelled");
    NSTask *task = [[NSTask alloc] init];
    task.launchPath = [[NSBundle mainBundle] executablePath];
    task.arguments = synthetic ? @[@"--internal-test-sleep"] : @[@"--internal-menu-trace"];
    NSPipe *pipe = [NSPipe pipe];
    task.standardOutput = pipe;
    task.standardError = pipe;
    int fd = pipe.fileHandleForReading.fileDescriptor;
    int flags = fcntl(fd, F_GETFL);
    if (flags < 0 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) < 0)
        return IncompleteMenuTrace(@"", @"capture unavailable");
    NSMutableData *captured = [NSMutableData data];
    BOOL truncated = NO;
    NSString *reason = nil;
    NSTimeInterval started = [[NSProcessInfo processInfo] systemUptime];
    @try {
        [task launch];
        while (task.running) {
            if (!DrainMenuTrace(fd, captured, &truncated)) reason = @"capture failed";
            else if (token.isCancelled) reason = @"cancelled";
            else if ([[NSProcessInfo processInfo] systemUptime] - started >= timeout)
                reason = @"timeout";
            if (reason) { StopRoutineChild(task); break; }
            [NSThread sleepForTimeInterval:0.05];
        }
        [task waitUntilExit];
        if (!DrainMenuTrace(fd, captured, &truncated) && !reason) reason = @"capture failed";
        if (token.isCancelled) reason = @"cancelled";
        int code = task.terminationStatus;
        if (!reason && (task.terminationReason != NSTaskTerminationReasonExit ||
                        (code != 0 && code != 2))) reason = @"worker failed";
        if (!reason && truncated) reason = @"output truncated";
        NSString *text = [[NSString alloc] initWithData:captured encoding:NSUTF8StringEncoding];
        if (!text) { text = @""; reason = reason ?: @"invalid output"; }
        if (reason) text = IncompleteMenuTrace(text, reason);
        else if (code == 2 && [text containsString:@"PASS: battery="]) {
            reason = @"inconsistent worker status";
            text = IncompleteMenuTrace(text, reason);
        }
        return [text stringByAppendingFormat:@"\nDiagnostic exit: %d\nElapsed ms: %.0f",
            reason ? ([reason isEqualToString:@"timeout"] ? 124 :
                [reason isEqualToString:@"cancelled"] ? 125 : 1) : code,
            ([[NSProcessInfo processInfo] systemUptime] - started) * 1000];
    } @catch (NSException *exception) {
        (void)exception;
        if (task.running) StopRoutineChild(task);
        return IncompleteMenuTrace(@"", @"capture unavailable");
    }
}

/// Synthetic evidence only: require the observed worker PID to be gone.
static BOOL MenuTraceChildReaped(NSString *trace) {
    NSRange marker = [trace rangeOfString:@"TEST: worker started; pid="];
    if (marker.location == NSNotFound) return NO;
    NSScanner *scanner = [NSScanner scannerWithString:
        [trace substringFromIndex:NSMaxRange(marker)]];
    int pid = 0;
    return [scanner scanInt:&pid] && pid > 1 && kill((pid_t)pid, 0) < 0 && errno == ESRCH;
}

@interface LegacyTray : NSObject <NSApplicationDelegate, NSMenuDelegate, CBCentralManagerDelegate,
                                   CBPeripheralDelegate>
@property(nonatomic, strong) NSStatusItem *tray;
@property(nonatomic, strong) NSMenuItem *detail;
@property(nonatomic, strong) NSTimer *timer;
@property(nonatomic, strong) CBCentralManager *central;
@property(nonatomic, strong) CBPeripheral *selectedPeripheral;
@property(nonatomic, strong) NSArray<CBPeripheral *> *connectedMice;
@property(nonatomic, assign) BatteryReading latest;
@property(nonatomic, strong) NSDate *sessionVerifiedAt;
@property(nonatomic, assign) BOOL polling;
@property(nonatomic, assign) BOOL isolatedPolling;
@property(nonatomic, assign) BOOL closing;
@property(nonatomic, assign) uint64_t journalFailedWrites;
@property(nonatomic, assign) AjazzDiagnosticSession *diagnosticSession;
@property(nonatomic, strong) NSMenuItem *sessionStatusItem;
@property(nonatomic, strong) NSMenuItem *sessionStartItem;
@property(nonatomic, strong) NSArray<NSMenuItem *> *sessionCaptureItems;
@property(nonatomic, strong) NSMenuItem *sessionSaveItem;
@property(nonatomic, strong) NSMenuItem *sessionDiscardItem;
@property(nonatomic, assign) BOOL diagnosticRunning;
@property(nonatomic, strong) LegacyPollCancellation *diagnosticCancellation;
@property(nonatomic, strong) NSMenuItem *runDiagnosticItem;
@property(nonatomic, strong) NSMenuItem *cancelDiagnosticItem;
@property(nonatomic, strong) LegacyPollCancellation *activeCancellation;
@property(nonatomic, assign) NSUInteger pollAttempt;
@property(nonatomic, assign) BOOL everConnected;
@property(nonatomic, assign) BOOL disconnectSent;
@property(nonatomic, assign) NSInteger absentCount;
@property(nonatomic, assign) NSUInteger alerted;
@property(nonatomic, assign) BOOL bluetoothRequested;
@property(nonatomic, assign) NSUInteger bluetoothRequestGeneration;
@property(nonatomic, assign) NSUInteger bluetoothAttempt;
@property(nonatomic, assign) NSTimeInterval bluetoothStarted;
@property(nonatomic, strong) NSString *bluetoothLastRead;
@property(nonatomic, strong) NSString *bluetoothDiscovery;
@end

@implementation LegacyTray

- (void)dealloc { AjazzSessionDestroy(self.diagnosticSession); }

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
    self.latest = (BatteryReading){BatteryChecking, -1, 0};
    self.diagnosticSession = AjazzSessionCreate();
    NSApp.applicationIconImage = AppearanceAppIcon(AppearanceChoice(@"ApplicationIconColor"));
    [self buildMenu];
    [self recordJournalEvent:AjazzEventStarted reason:AjazzReasonNone];
    if (self.isolatedPolling)
        [self recordJournalEvent:AjazzEventIsolatedPollingEnabled reason:AjazzReasonNone];
    [self scheduleTimer];
    [self refresh:nil];
}

/// Record closed GUI events; journal failure never blocks normal operation.
- (void)recordJournalEvent:(AjazzOperationalEvent)event reason:(AjazzOperationalReason)reason {
    [self recordJournalEvent:event reason:reason durationMs:-1];
}

- (void)recordJournalEvent:(AjazzOperationalEvent)event reason:(AjazzOperationalReason)reason
                durationMs:(int64_t)durationMs {
    NSURL *support = [[[NSFileManager defaultManager]
        URLsForDirectory:NSApplicationSupportDirectory inDomains:NSUserDomainMask] firstObject];
    if (!AjazzJournalEditionTimedEvent(support.fileSystemRepresentation, true, event, reason,
                                      time(NULL), durationMs) &&
        self.journalFailedWrites < UINT64_MAX) self.journalFailedWrites++;
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    [self recordJournalEvent:AjazzEventStopped reason:AjazzReasonNone];
}

- (NSString *)appearanceLabel:(NSString *)color {
    if ([color isEqualToString:@"white"]) return [self word:@"White" ru:@"Белый" uk:@"Білий"];
    if ([color isEqualToString:@"black"]) return [self word:@"Black" ru:@"Чёрный" uk:@"Чорний"];
    if ([color isEqualToString:@"blue"]) return [self word:@"Blue" ru:@"Синий" uk:@"Синій"];
    return [self word:@"Orange" ru:@"Оранжевый" uk:@"Помаранчевий"];
}

- (NSMenuItem *)appearanceMenu:(NSString *)title key:(NSString *)key {
    NSMenuItem *parent = [[NSMenuItem alloc] initWithTitle:title action:NULL keyEquivalent:@""];
    NSMenu *menu = [[NSMenu alloc] initWithTitle:title];
    for (NSString *color in AppearanceChoices()) {
        NSMenuItem *item = [self item:menu title:[self appearanceLabel:color] action:@selector(selectAppearance:)];
        item.representedObject = @[key, color];
        item.state = [AppearanceChoice(key) isEqualToString:color] ? NSControlStateValueOn : NSControlStateValueOff;
        if ([key isEqualToString:@"ApplicationIconColor"]) {
            NSImage *image = AppearanceAppIcon(color);
            image.size = NSMakeSize(16, 16);
            item.image = image;
        } else if ([key isEqualToString:@"TrayIconColor"]) {
            item.image = AppearanceTrayImage(83, color, YES);
        }
    }
    parent.submenu = menu;
    return parent;
}

- (void)selectAppearance:(NSMenuItem *)sender {
    NSArray *value = sender.representedObject;
    if (![value isKindOfClass:NSArray.class] || value.count != 2 ||
        ![@[@"ApplicationIconColor", @"TrayIconColor"] containsObject:value[0]] ||
        ![AppearanceChoices() containsObject:value[1]]) return;
    [[NSUserDefaults standardUserDefaults] setObject:value[1] forKey:value[0]];
    if ([value[0] isEqualToString:@"ApplicationIconColor"])
        NSApp.applicationIconImage = AppearanceAppIcon(value[1]);
    [self buildMenu];
}

- (void)toggleTrayStyle:(id)sender {
    [[NSUserDefaults standardUserDefaults] setBool:!AppearanceMouseStyle() forKey:@"MouseTrayIcon"];
    [self buildMenu];
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
    NSMenu *diagnostics = [[NSMenu alloc] initWithTitle:@"Diagnostics"];
    diagnostics.autoenablesItems = NO;
    [self item:diagnostics title:[self word:@"Device diagnostics…" ru:@"Диагностика устройства…" uk:@"Діагностика пристрою…"]
                   action:@selector(showDiagnostics:)];
    self.runDiagnosticItem = [self item:diagnostics title:[self word:@"Run HID diagnostics…" ru:@"Запустить HID-диагностику…" uk:@"Запустити HID-діагностику…"]
                   action:@selector(runHIDDiagnostics:)];
    self.cancelDiagnosticItem = [self item:diagnostics
        title:[self word:@"Cancel HID diagnostics" ru:@"Отменить HID-диагностику" uk:@"Скасувати HID-діагностику"]
        action:@selector(cancelHIDDiagnostics:)];
    [self updateDiagnosticMenu];
    [self item:diagnostics title:[self word:@"Copy diagnostics" ru:@"Копировать диагностику" uk:@"Копіювати діагностику"]
                   action:@selector(copyDiagnostics:)];
    NSMenuItem *session = [diagnostics addItemWithTitle:
        [self word:@"Diagnostic session" ru:@"Сеанс диагностики" uk:@"Сеанс діагностики"]
        action:NULL keyEquivalent:@""];
    session.submenu = [self buildDiagnosticSessionMenu];
    NSMenuItem *diagnosticItem = [menu addItemWithTitle:
        [self word:@"Diagnostics" ru:@"Диагностика" uk:@"Діагностика"] action:NULL keyEquivalent:@""];
    diagnosticItem.submenu = diagnostics;
    [menu addItem:[NSMenuItem separatorItem]];

    NSMenu *settings = [[NSMenu alloc] initWithTitle:@"Settings"];
    [settings addItem:[self appearanceMenu:[self word:@"Application icon" ru:@"Иконка приложения" uk:@"Значок застосунку"]
        key:@"ApplicationIconColor"]];
    [settings addItem:[self appearanceMenu:[self word:@"Tray icon color" ru:@"Цвет иконки" uk:@"Колір значка"]
        key:@"TrayIconColor"]];
    NSMenuItem *style = [self item:settings title:[self word:@"Mouse-shaped tray icon" ru:@"Значок мыши" uk:@"Значок миші"]
        action:@selector(toggleTrayStyle:)];
    style.state = AppearanceMouseStyle() ? NSControlStateValueOn : NSControlStateValueOff;
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
    menu.delegate = self;
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
    if (self.closing) return;
    self.timer = [NSTimer scheduledTimerWithTimeInterval:(NSTimeInterval)[self interval]
        target:self selector:@selector(refresh:) userInfo:nil repeats:YES];
}

- (void)display:(BatteryReading)reading {
    reading = PresentationReading(reading, self.sessionVerifiedAt, [NSDate date]);
    if (reading.state == BatteryValid) {
        self.tray.button.title = [NSString stringWithFormat:@"🔋%ld%%",
                                 (long)reading.percent];
        self.detail.title = [NSString stringWithFormat:@"AJAZZ APEX: %ld%%",
                             (long)reading.percent];
    } else if (reading.state == BatteryChecking) {
        self.tray.button.title = @"AJAZZ ?";
        self.detail.title = [self word:@"Checking USB receiver…"
                                    ru:@"Проверка USB-приёмника…"
                                    uk:@"Перевірка USB-приймача…"];
    } else if (reading.state == BatteryAbsent) {
        self.tray.button.title = @"AJAZZ —";
        self.detail.title = [self word:@"Compatible receiver not found"
                                       ru:@"Совместимый приёмник не найден"
                                       uk:@"Сумісний приймач не знайдено"];
    } else if (reading.state == BatteryAccessError) {
        self.tray.button.title = @"AJAZZ !";
        self.detail.title = [self word:@"Cannot access receiver HID interface"
                                       ru:@"Нет доступа к HID-интерфейсу"
                                       uk:@"Немає доступу до HID-інтерфейсу"];
    } else if (reading.state == BatteryTimedOut) {
        self.tray.button.title = @"AJAZZ !";
        self.detail.title = self.isolatedPolling
            ? [self word:@"HID read timed out"
                      ru:@"Тайм-аут чтения HID"
                      uk:@"Час очікування читання HID вичерпано"]
            : [self word:@"HID read stalled; restart app if persistent"
                      ru:@"Чтение HID зависло; перезапустите приложение"
                      uk:@"Читання HID зависло; перезапустіть застосунок"];
    } else if (reading.state == BatteryUnexpectedUsage) {
        self.tray.button.title = @"AJAZZ ?";
        self.detail.title = [self word:@"Receiver HID collection not supported"
                                       ru:@"HID-интерфейс приёмника не поддерживается"
                                       uk:@"HID-інтерфейс приймача не підтримується"];
    } else {
        self.tray.button.title = @"AJAZZ ?";
        self.detail.title = [self word:@"Receiver present; battery unknown"
                                       ru:@"Приёмник найден, заряд неизвестен"
                                       uk:@"Приймач знайдено, заряд невідомий"];
    }
    if (self.sessionVerifiedAt && reading.state != BatteryValid) {
        NSString *stamp = [NSDateFormatter localizedStringFromDate:self.sessionVerifiedAt
            dateStyle:NSDateFormatterShortStyle timeStyle:NSDateFormatterMediumStyle];
        NSString *format = [self word:@"Last verified USB sample (session): %@"
            ru:@"Последнее подтверждённое USB-измерение (сеанс): %@"
            uk:@"Останнє підтверджене USB-вимірювання (сеанс): %@"];
        self.detail.title = [self.detail.title stringByAppendingFormat:@" · %@",
                            [NSString stringWithFormat:format, stamp]];
    }
    NSString *color = AppearanceChoice(@"TrayIconColor");
    self.tray.button.title = @"";
    self.tray.button.image = AppearanceTrayImage(
        reading.state == BatteryValid ? reading.percent : -1, color, AppearanceMouseStyle());
    [self updateDiagnosticMenu];
    self.tray.button.toolTip = [self.detail.title stringByAppendingFormat:@" · %@", [self appearanceLabel:color]];
}

- (void)notify:(NSString *)title message:(NSString *)message {
    NSUserNotification *note = [[NSUserNotification alloc] init];
    note.title = title;
    note.informativeText = message;
    [[NSUserNotificationCenter defaultUserNotificationCenter]
        deliverNotification:note];
}

- (void)evaluateAlerts:(BatteryReading)reading {
    if (reading.state != BatteryValid && reading.state != BatteryAbsent) {
        // No valid battery report: never treat errors as 0% or disconnected.
        self.absentCount = 0;
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
    const NSInteger levels[] = {50, 25, 10};
    NSUInteger crossed = 0;
    for (NSUInteger i = 0; i < 3; i++) {
        NSUInteger bit = 1U << i;
        if (reading.percent >= levels[i] + 5) self.alerted &= ~bit;
        if (reading.percent < levels[i]) crossed |= bit;
    }
    if (![self setting:@"LegacyNotifyLow"] ||
        !(crossed & [self thresholdMask] & ~self.alerted)) return;
    self.alerted |= crossed;
    [self notify:@"AJAZZ APEX" message:
        [NSString stringWithFormat:
         [self word:@"Low battery: %ld%%" ru:@"Низкий заряд: %ld%%"
                     uk:@"Низький заряд: %ld%%"], (long)reading.percent]];
}

- (void)menuWillOpen:(NSMenu *)menu {
    (void)menu;
    [self display:self.latest];
}

- (void)refresh:(id)sender {
    if (self.closing) return;
    if (PresentationReading(self.latest, self.sessionVerifiedAt, [NSDate date]).state != self.latest.state)
        [self display:self.latest];
    if (self.polling || self.diagnosticRunning || self.closing) return; // Never accumulate blocked HID threads.
    self.polling = YES;
    LegacyPollCancellation *token = self.isolatedPolling
        ? [[LegacyPollCancellation alloc] init] : nil;
    self.activeCancellation = token;
    NSUInteger attempt = ++self.pollAttempt;
    __weak LegacyTray *weakSelf = self;
    if (!token) dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 20 * NSEC_PER_SEC),
                   dispatch_get_main_queue(), ^{
        LegacyTray *owner = weakSelf;
        if (!owner || !owner.polling || owner.pollAttempt != attempt) return;
        if (!owner.closing)
            [owner recordJournalEvent:AjazzEventPollFailed reason:AjazzReasonTimeout];
        owner.latest = (BatteryReading){BatteryTimedOut, -1, 0};
        [owner display:owner.latest];
        // Keep the single-flight guard until the original IOKit call returns.
    });
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        @autoreleasepool {
            NSTimeInterval readStart = [[NSProcessInfo processInfo] systemUptime];
            BatteryReading reading = token
                ? RunRoutine(@"--internal-routine-read", 8, token) : ReadReceiver();
            int64_t readMs = AjazzElapsedMilliseconds(readStart,
                [[NSProcessInfo processInfo] systemUptime]);
            NSDate *observedAt = [NSDate date];
            dispatch_async(dispatch_get_main_queue(), ^{
                LegacyTray *owner = weakSelf;
                if (!owner || owner.pollAttempt != attempt) return;
                owner.polling = NO;
                owner.activeCancellation = nil;
                if (owner.closing) {
                    [NSApp replyToApplicationShouldTerminate:YES];
                    return;
                }
                if (token && reading.state == BatteryTimedOut)
                    [owner recordJournalEvent:AjazzEventIsolatedPollTimedOut reason:AjazzReasonTimeout
                                       durationMs:readMs];
                owner.sessionVerifiedAt = SessionVerifiedAt(owner.sessionVerifiedAt,
                                                            reading, observedAt);
                owner.latest = reading;
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

- (NSMenu *)buildDiagnosticSessionMenu {
    NSMenu *menu = [[NSMenu alloc] initWithTitle:@"Diagnostic session"];
    menu.autoenablesItems = NO;
    self.sessionStatusItem = [menu addItemWithTitle:@"" action:NULL keyEquivalent:@""];
    self.sessionStatusItem.enabled = NO;
    self.sessionStartItem = [self item:menu
        title:[self word:@"Start diagnostic session" ru:@"Начать сеанс диагностики" uk:@"Почати сеанс діагностики"]
        action:@selector(startDiagnosticSession:)];
    NSArray *labels = @[
        [self word:@"Capture baseline" ru:@"Снять исходное состояние" uk:@"Зняти початковий стан"],
        [self word:@"Mark 2.4 GHz selected" ru:@"Отметить выбор 2,4 ГГц" uk:@"Позначити вибір 2,4 ГГц"],
        [self word:@"Mark Bluetooth selected" ru:@"Отметить выбор Bluetooth" uk:@"Позначити вибір Bluetooth"],
        [self word:@"Mark sleep" ru:@"Отметить сон" uk:@"Позначити сон"],
        [self word:@"Mark wake" ru:@"Отметить пробуждение" uk:@"Позначити пробудження"],
        [self word:@"Capture another snapshot" ru:@"Снять ещё один снимок" uk:@"Зняти ще один знімок"]
    ];
    NSMutableArray *items = [NSMutableArray array];
    for (NSUInteger i = 0; i < labels.count; i++) {
        NSMenuItem *item = [self item:menu title:labels[i] action:@selector(captureDiagnosticMarker:)];
        item.tag = (NSInteger)i;
        [items addObject:item];
    }
    self.sessionCaptureItems = items;
    self.sessionSaveItem = [self item:menu
        title:[self word:@"Save diagnostic session…" ru:@"Сохранить сеанс диагностики…" uk:@"Зберегти сеанс діагностики…"]
        action:@selector(saveDiagnosticSession:)];
    self.sessionDiscardItem = [self item:menu
        title:[self word:@"Discard diagnostic session" ru:@"Удалить сеанс диагностики" uk:@"Видалити сеанс діагностики"]
        action:@selector(discardDiagnosticSession:)];
    [self updateSessionMenu];
    return menu;
}

- (void)updateSessionMenu {
    BOOL active = AjazzSessionActive(self.diagnosticSession);
    unsigned count = AjazzSessionCount(self.diagnosticSession);
    self.sessionStatusItem.title = [NSString stringWithFormat:@"%@: %u/32",
        [self word:@"Snapshots" ru:@"Снимки" uk:@"Знімки"], count];
    self.sessionStartItem.enabled = !self.closing && !active && self.diagnosticSession != NULL;
    for (NSMenuItem *item in self.sessionCaptureItems)
        item.enabled = !self.closing && active && count < AJAZZ_SESSION_LIMIT;
    self.sessionSaveItem.enabled = !self.closing && active && count >= 2;
    self.sessionDiscardItem.enabled = !self.closing && active;
}

- (void)startDiagnosticSession:(id)sender {
    (void)sender;
    if (self.closing) return;
    AjazzSessionStart(self.diagnosticSession);
    [self updateSessionMenu];
}

- (void)addSessionReport:(NSString *)report marker:(unsigned)marker {
    if (self.closing || !AjazzSessionActive(self.diagnosticSession)) return;
    NSData *data = [report dataUsingEncoding:NSUTF8StringEncoding];
    BOOL added = AjazzSessionAdd(self.diagnosticSession, marker, data.bytes, data.length);
    [self updateSessionMenu];
    [self message:added ? [self word:@"Snapshot added" ru:@"Снимок добавлен" uk:@"Знімок додано"] :
        [self word:@"Snapshot not added; wait a second or check session limits"
            ru:@"Снимок не добавлен; подождите секунду или проверьте лимиты сеанса"
            uk:@"Знімок не додано; зачекайте секунду або перевірте ліміти сеансу"]];
}

- (void)captureDiagnosticMarker:(NSMenuItem *)sender {
    if (self.closing || sender.tag < 0 || sender.tag > 5) return;
    [self addSessionReport:[self diagnostics] marker:(unsigned)sender.tag];
}

- (void)discardDiagnosticSession:(id)sender {
    (void)sender;
    if (self.closing || !AjazzSessionActive(self.diagnosticSession)) return;
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = [self word:@"Discard all session snapshots?" ru:@"Удалить все снимки сеанса?" uk:@"Видалити всі знімки сеансу?"];
    [alert addButtonWithTitle:[self word:@"Discard" ru:@"Удалить" uk:@"Видалити"]];
    [alert addButtonWithTitle:[self word:@"Close" ru:@"Закрыть" uk:@"Закрити"]];
    [NSApp activateIgnoringOtherApps:YES];
    if ([alert runModal] == NSAlertFirstButtonReturn && !self.closing) {
        AjazzSessionClear(self.diagnosticSession);
        [self updateSessionMenu];
    }
}

- (void)saveDiagnosticSession:(id)sender {
    (void)sender;
    if (self.closing || AjazzSessionCount(self.diagnosticSession) < 2) return;
    NSSavePanel *panel = [NSSavePanel savePanel];
    panel.nameFieldStringValue = @"ajazz-high-sierra-diagnostic-session.zip";
    panel.allowedFileTypes = @[@"zip"];
    panel.message = [self word:@"Session may contain reply bytes. Review before sharing."
        ru:@"Сеанс может содержать байты ответа. Проверьте перед отправкой."
        uk:@"Сеанс може містити байти відповіді. Перевірте перед надсиланням."];
    [NSApp activateIgnoringOtherApps:YES];
    if ([panel runModal] != NSModalResponseOK || !panel.URL || self.closing) return;
    if (!AjazzSessionSave(self.diagnosticSession, panel.URL.path.fileSystemRepresentation))
        [self message:[self word:@"Unable to save a new diagnostic file" ru:@"Не удалось сохранить новый файл отчёта" uk:@"Не вдалося зберегти новий файл звіту"]];
}

- (NSString *)diagnostics {
    BatteryReading current = PresentationReading(self.latest, self.sessionVerifiedAt, [NSDate date]);
    NSString *state = current.state == BatteryValid ? @"valid" :
        (current.state == BatteryChecking ? @"not checked yet" :
         current.state == BatteryAbsent ? @"not connected" :
         current.state == BatteryAccessError ? @"access error" :
         current.state == BatteryUnexpectedUsage ? @"HID usage mismatch" :
         current.state == BatteryTimedOut ? @"HID read stalled" :
         @"receiver present, no valid battery");
    NSISO8601DateFormatter *utc = [[NSISO8601DateFormatter alloc] init];
    NSString *sample = self.sessionVerifiedAt ? [utc stringFromDate:self.sessionVerifiedAt] : @"never";
    NSString *battery = current.state == BatteryValid ?
        [NSString stringWithFormat:@"%ld%%", (long)current.percent] : @"unknown";
    return [NSString stringWithFormat:
        @"AJAZZ Battery Tray High Sierra Edition\nReport schema: apple-menu-v1\nVersion: %@ (%@)\nUTC: %@\n"
         @"OS: %@\nVID:PID: 3151:5007\nUsage: FFFF:0002\n"
         @"Battery state: %@; battery: %@\nMatching HID collections: %ld\n"
         @"Last verified USB UTC (session): %@\nPolling active: %@; isolated: %@\n"
         @"Operational journal failed writes (process): %llu\n"
         @"Bluetooth discovery: %@\nBluetooth manual 180F/2A19 pending: %@\n"
         @"Bluetooth last manual read: %@\n"
         @"Firmware and device serial numbers were not queried.",
         [[NSBundle mainBundle] objectForInfoDictionaryKey:@"CFBundleShortVersionString"],
         [[NSBundle mainBundle] objectForInfoDictionaryKey:@"CFBundleVersion"],
         [utc stringFromDate:[NSDate dateWithTimeIntervalSince1970:floor([[NSDate date] timeIntervalSince1970])]], [[NSProcessInfo processInfo] operatingSystemVersionString],
         state, battery, (long)current.collections, sample,
         self.polling ? @"True" : @"False", self.isolatedPolling ? @"True" : @"False",
         (unsigned long long)self.journalFailedWrites,
         self.bluetoothDiscovery ?: @"not requested", self.selectedPeripheral ? @"True" : @"False",
         self.bluetoothLastRead ?: @"not requested"];
}

- (void)copyReport:(NSString *)report {
    NSPasteboard *board = [NSPasteboard generalPasteboard];
    [board clearContents];
    if (![board setString:report forType:NSPasteboardTypeString])
        [self message:[self word:@"Unable to copy diagnostics" ru:@"Не удалось скопировать отчёт" uk:@"Не вдалося скопіювати звіт"]];
}

- (void)copyDiagnostics:(id)sender { [self copyReport:[self diagnostics]]; }

- (void)saveReport:(NSString *)report {
    NSSavePanel *panel = [NSSavePanel savePanel];
    panel.nameFieldStringValue = @"ajazz-high-sierra-diagnostics.txt";
    if ([panel runModal] != NSModalResponseOK || !panel.URL) return;
    NSData *data = [report dataUsingEncoding:NSUTF8StringEncoding];
    if (AjazzWriteDiagnostic(panel.URL.path.fileSystemRepresentation, data.bytes, data.length) != 0)
        [self message:[self word:@"Unable to save a new diagnostic file" ru:@"Не удалось сохранить новый файл отчёта" uk:@"Не вдалося зберегти новий файл звіту"]];
}

- (void)reviewReport:(NSString *)report {
    NSAlert *alert = [[NSAlert alloc] init];
    alert.messageText = [self word:@"Device diagnostics" ru:@"Диагностика устройства" uk:@"Діагностика пристрою"];
    NSScrollView *scroll = [[NSScrollView alloc] initWithFrame:NSMakeRect(0, 0, 470, 260)];
    NSTextView *view = [[NSTextView alloc] initWithFrame:scroll.bounds];
    view.string = report;
    view.editable = NO;
    view.selectable = YES;
    view.verticallyResizable = YES;
    view.autoresizingMask = NSViewWidthSizable;
    scroll.documentView = view;
    scroll.hasVerticalScroller = YES;
    alert.accessoryView = scroll;
    [alert addButtonWithTitle:[self word:@"Copy report" ru:@"Копировать" uk:@"Копіювати"]];
    [alert addButtonWithTitle:[self word:@"Save report…" ru:@"Сохранить…" uk:@"Зберегти…"]];
    [alert addButtonWithTitle:[self word:@"Close" ru:@"Закрыть" uk:@"Закрити"]];
    if (AjazzSessionActive(self.diagnosticSession))
        [alert addButtonWithTitle:[self word:@"Add report to diagnostic session" ru:@"Добавить отчёт в сеанс" uk:@"Додати звіт до сеансу"]];
    [NSApp activateIgnoringOtherApps:YES];
    NSModalResponse result = [alert runModal];
    if (result == NSAlertFirstButtonReturn) [self copyReport:report];
    if (result == NSAlertSecondButtonReturn) [self saveReport:report];
    if (result == NSAlertThirdButtonReturn + 1) [self addSessionReport:report marker:6];
}

- (void)showDiagnostics:(id)sender { [self reviewReport:[self diagnostics]]; }

- (void)updateDiagnosticMenu {
    self.runDiagnosticItem.enabled = !self.diagnosticRunning && !self.closing;
    self.cancelDiagnosticItem.enabled = self.diagnosticRunning && !self.closing &&
        self.diagnosticCancellation && !self.diagnosticCancellation.isCancelled;
    if (self.diagnosticRunning) {
        self.detail.title = self.diagnosticCancellation.isCancelled ?
            [self word:@"Cancelling HID diagnostics…" ru:@"Отмена HID-диагностики…" uk:@"Скасування HID-діагностики…"] :
            [self word:@"Running HID diagnostics…" ru:@"Выполняется HID-диагностика…" uk:@"Виконується HID-діагностика…"];
    }
}

- (void)cancelHIDDiagnostics:(id)sender {
    if (!self.diagnosticRunning || self.closing || !self.diagnosticCancellation ||
        self.diagnosticCancellation.isCancelled) return;
    self.diagnosticCancellation.cancelled = YES;
    [self updateDiagnosticMenu];
}

- (void)runHIDDiagnostics:(id)sender {
    if (self.polling || self.diagnosticRunning || self.closing) {
        [self message:[self word:@"Diagnostic busy; try again after the current read" ru:@"Идёт опрос; повторите после завершения" uk:@"Триває опитування; повторіть після завершення"]];
        return;
    }
    NSAlert *consent = [[NSAlert alloc] init];
    consent.messageText = [self word:@"Run HID diagnostics" ru:@"Запустить HID-диагностику" uk:@"Запустити HID-діагностику"];
    consent.informativeText = [self word:@"F7/05 query, up to 20 seconds. First 8 reply bytes included. No RTC or configuration writes. Review before sharing."
        ru:@"Опрос F7/05, до 20 секунд. Первые 8 байт ответа. Без RTC и настроек. Проверьте перед отправкой."
        uk:@"Опитування F7/05, до 20 секунд. Перші 8 байтів відповіді. Без RTC і налаштувань. Перевірте перед надсиланням."];
    [consent addButtonWithTitle:[self word:@"Run" ru:@"Запустить" uk:@"Запустити"]];
    [consent addButtonWithTitle:[self word:@"Cancel" ru:@"Отмена" uk:@"Скасувати"]];
    [NSApp activateIgnoringOtherApps:YES];
    if ([consent runModal] != NSAlertFirstButtonReturn || self.polling || self.diagnosticRunning || self.closing) return;
    self.diagnosticRunning = YES;
    LegacyPollCancellation *token = [[LegacyPollCancellation alloc] init];
    self.diagnosticCancellation = token;
    NSString *snapshot = [self diagnostics];
    [self updateDiagnosticMenu];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{
        @autoreleasepool {
            NSString *trace = CaptureMenuTrace(NO, token, 20);
            dispatch_async(dispatch_get_main_queue(), ^{
                self.diagnosticCancellation = nil;
                if (self.closing) {
                    self.diagnosticRunning = NO;
                    [NSApp replyToApplicationShouldTerminate:YES];
                    return;
                }
                self.diagnosticRunning = NO;
                [self display:self.latest];
                [self updateDiagnosticMenu];
                NSString *result = token.isCancelled && ![trace hasPrefix:@"INCOMPLETE: cancelled;"] ?
                    IncompleteMenuTrace([trace stringByAppendingString:@"\n"], @"cancelled") : trace;
                [self reviewReport:[snapshot stringByAppendingFormat:@"\n\nFresh bounded F7/05 trace:\n%@", result]];
            });
        }
    });
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
    self.bluetoothDiscovery = @"checking access";
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
        self.bluetoothDiscovery = @"initialization timeout";
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
        self.bluetoothDiscovery = [NSString stringWithFormat:@"access unavailable; state=%ld", (long)central.state];
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
    self.bluetoothDiscovery = [NSString stringWithFormat:@"connected candidates=%lu", (unsigned long)matching.count];
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
    self.bluetoothStarted = [[NSProcessInfo processInfo] systemUptime];
    NSUInteger attempt = self.bluetoothAttempt;
    self.selectedPeripheral.delegate = self;
    [central connectPeripheral:self.selectedPeripheral options:nil];
    CBPeripheral *pending = self.selectedPeripheral;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 10 * NSEC_PER_SEC),
                   dispatch_get_main_queue(), ^{
        // A previous attempt must not terminate a newer read of the same mouse.
        if (self.selectedPeripheral == pending && self.bluetoothAttempt == attempt) {
            [self finishBluetooth:@"Bluetooth Battery Service timed out." outcome:@"timeout" percent:nil];
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
        [self finishBluetooth:@"Failed to read connected Bluetooth mouse." outcome:@"connection failed" percent:nil];
}

- (void)peripheral:(CBPeripheral *)device didDiscoverServices:(NSError *)error {
    if (device != self.selectedPeripheral) return;
    if (error) {
        [self finishBluetooth:@"Bluetooth service discovery failed." outcome:@"service discovery failed" percent:nil];
        return;
    }
    for (CBService *service in device.services) {
        if ([service.UUID isEqual:[CBUUID UUIDWithString:@"180F"]]) {
            [device discoverCharacteristics:@[[CBUUID UUIDWithString:@"2A19"]]
                                 forService:service];
            return;
        }
    }
    [self finishBluetooth:@"Battery Service (180F) is unavailable." outcome:@"service unavailable" percent:nil];
}

- (void)peripheral:(CBPeripheral *)device didDiscoverCharacteristicsForService:
    (CBService *)service error:(NSError *)error {
    if (device != self.selectedPeripheral || ![service.UUID isEqual:[CBUUID UUIDWithString:@"180F"]]) return;
    if (error) {
        [self finishBluetooth:@"Bluetooth characteristic discovery failed." outcome:@"characteristic discovery failed" percent:nil];
        return;
    }
    for (CBCharacteristic *characteristic in service.characteristics) {
        if ([characteristic.UUID isEqual:[CBUUID UUIDWithString:@"2A19"]]) {
            [device readValueForCharacteristic:characteristic];
            return;
        }
    }
    [self finishBluetooth:@"Battery Level (2A19) is unavailable." outcome:@"characteristic unavailable" percent:nil];
}

- (void)peripheral:(CBPeripheral *)device didUpdateValueForCharacteristic:
    (CBCharacteristic *)characteristic error:(NSError *)error {
    if (device != self.selectedPeripheral || ![characteristic.UUID isEqual:[CBUUID UUIDWithString:@"2A19"]] ||
        ![characteristic.service.UUID isEqual:[CBUUID UUIDWithString:@"180F"]]) return;
    NSData *value = characteristic.value;
    if (!error && value.length == 1 && ((const uint8_t *)value.bytes)[0] <= 100) {
        NSNumber *percent = @(((const uint8_t *)value.bytes)[0]);
        [self finishBluetooth:[NSString stringWithFormat:@"Bluetooth battery: %@%%", percent]
            outcome:@"fresh GATT" percent:percent];
    } else {
        [self finishBluetooth:@"No valid Bluetooth Battery Level returned." outcome:@"invalid reply" percent:nil];
    }
}

- (void)centralManager:(CBCentralManager *)central
    didDisconnectPeripheral:(CBPeripheral *)device error:(NSError *)error {
    if (device == self.selectedPeripheral && device.state == CBPeripheralStateDisconnected) {
        [self finishBluetooth:@"Bluetooth mouse disconnected before the read completed." outcome:@"disconnected" percent:nil];
    }
}

- (void)finishBluetooth:(NSString *)message outcome:(NSString *)outcome percent:(NSNumber *)percent {
    if (!self.selectedPeripheral) return;
    NSString *level = percent ? [NSString stringWithFormat:@"%@%%", percent] : @"unknown";
    NSISO8601DateFormatter *utc = [[NSISO8601DateFormatter alloc] init];
    NSTimeInterval elapsed = [[NSProcessInfo processInfo] systemUptime] - self.bluetoothStarted;
    self.bluetoothLastRead = [NSString stringWithFormat:
        @"outcome=%@; battery=%@; UTC=%@; elapsed_ms=%.0f",
        outcome, level, [utc stringFromDate:[NSDate date]], elapsed * 1000];
    self.selectedPeripheral.delegate = nil;
    [self.central cancelPeripheralConnection:self.selectedPeripheral];
    self.selectedPeripheral = nil;
    [self message:message];
}

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender {
    if (self.diagnosticRunning) {
        self.closing = YES;
        [self.timer invalidate];
        self.diagnosticCancellation.cancelled = YES;
        return NSTerminateLater;
    }
    if (!self.isolatedPolling || !self.polling) return NSTerminateNow;
    self.closing = YES;
    [self.timer invalidate];
    self.activeCancellation.cancelled = YES;
    return NSTerminateLater;
}

- (void)quit:(id)sender { [NSApp terminate:nil]; }
@end


/// Distinguish no verified reply from a validated percentage.
static int DiagnoseReceiver(void) {
    puts("STEP: enumerate receiver and request F7/05 telemetry");
    BatteryReading reading = ReadReceiver();
    printf("VID:PID=3151:5007 matching_collections=%ld ",
           (long)reading.collections);
    if (reading.state == BatteryValid) {
        printf("PASS: battery=%ld%%\n", (long)reading.percent);
        return 0;
    }
    if (reading.state == BatteryAbsent)
        puts("INCONCLUSIVE: receiver not found");
    else if (reading.state == BatteryAccessError)
        puts("INCONCLUSIVE: HID manager/device access failed");
    else if (reading.state == BatteryUnexpectedUsage)
        puts("INCONCLUSIVE: HID usage FFFF:0002 not found");
    else
        puts("INCONCLUSIVE: receiver present; battery unverified");
    return 2;
}

@interface CorpusTray : LegacyTray
@property(nonatomic, assign) NSUInteger notifications;
@end
@implementation CorpusTray
- (BOOL)setting:(NSString *)key { (void)key; return YES; }
- (void)notify:(NSString *)title message:(NSString *)message {
    (void)title; (void)message;
    self.notifications++;
}
@end

static BOOL VerifyObservationCorpus(NSString *path) {
    NSString *text = [NSString stringWithContentsOfFile:path encoding:NSUTF8StringEncoding error:nil];
    if (!text) return NO;
    NSArray *rows = [text componentsSeparatedByCharactersInSet:[NSCharacterSet newlineCharacterSet]];
    NSUInteger count = 0;
    for (NSUInteger i = 1; i < rows.count; i++) {
        if (![rows[i] length]) continue;
        NSArray<NSString *> *fields = [rows[i] componentsSeparatedByString:@","];
        if (fields.count != 5 || fields[2].length % 2) return NO;
        NSMutableData *data = [NSMutableData data];
        for (NSUInteger j = 0; j < fields[2].length; j += 2) {
            NSString *pair = [fields[2] substringWithRange:NSMakeRange(j, 2)];
            NSScanner *scanner = [NSScanner scannerWithString:pair];
            unsigned int value = 0;
            if (![scanner scanHexInt:&value] || !scanner.isAtEnd || value > 255) return NO;
            uint8_t byte = (uint8_t)value;
            [data appendBytes:&byte length:1];
        }
        NSInteger percent = ParseBattery(data.bytes, data.length);
        NSString *result = percent < 0 ? @"unknown" : [NSString stringWithFormat:@"%ld", (long)percent];
        if (![result isEqualToString:fields[4]]) return NO;
        if (percent < 0) {
            CorpusTray *tray = [[CorpusTray alloc] init];
            [tray evaluateAlerts:(BatteryReading){BatteryValid, 83, 1}];
            [tray evaluateAlerts:(BatteryReading){BatteryAbsent, -1, 0}];
            [tray evaluateAlerts:(BatteryReading){BatteryUnknown, -1, 1}];
            [tray evaluateAlerts:(BatteryReading){BatteryAbsent, -1, 0}];
            if (tray.notifications != 0 || tray.absentCount != 1) return NO;
        }
        count++;
    }
    if (count != 20) return NO;
    puts("PASS: 20 shared F7 observations and alert policy (no notifications delivered)");
    return YES;
}

static int SelfTest(void) {
    if (!AppearanceSelfTest()) {
        puts("FAIL: bundled appearance resources or rendered critical state");
        return 1;
    }
    puts("PASS: four bundled app icons and 36 appearance rendering cases");
    uint8_t first[] = {5, 0, 0, 1};
    uint8_t full[] = {5, 0, 0, 100};
    uint8_t stripped[] = {0, 0, 25};
    uint8_t zero[] = {5, 0, 0, 0};
    uint8_t excess[] = {5, 0, 0, 101};
    uint8_t wrongID[] = {6, 0, 0, 83};
    uint8_t malformed[] = {5, 1, 0, 83};
    uint8_t shortFrame[] = {5, 0};
    uint8_t mouse[] = {5, 1, 0, 83, 1, 0, 1, 2, 0, 0};
    BOOL shared = ParseBattery(mouse, sizeof mouse) == 83 &&
        ParseBattery(mouse + 1, sizeof mouse - 1) == 83;
    mouse[1] = 0;
    shared = shared && ParseBattery(mouse, sizeof mouse) == -1;
    mouse[7] = 1;
    shared = shared && ParseBattery(mouse + 1, sizeof mouse - 1) == -1;
    LegacyTray *test = [[LegacyTray alloc] init];
    [test evaluateAlerts:(BatteryReading){BatteryAccessError, -1, 0}];
    [test evaluateAlerts:(BatteryReading){BatteryUnexpectedUsage, -1, 0}];
    [test evaluateAlerts:(BatteryReading){BatteryUnknown, -1, 0}];
    [test evaluateAlerts:(BatteryReading){BatteryTimedOut, -1, 0}];
    BOOL safe = !test.everConnected && test.absentCount == 0 &&
        test.alerted == 0;
    NSDate *stamp = [NSDate dateWithTimeIntervalSince1970:12345];
    NSDate *verified = SessionVerifiedAt(nil, (BatteryReading){BatteryValid, 83, 1}, stamp);
    BOOL provenance = [verified isEqualToDate:stamp] &&
        [SessionVerifiedAt(verified, (BatteryReading){BatteryTimedOut, -1, 0},
            [stamp dateByAddingTimeInterval:30]) isEqualToDate:stamp] &&
        SessionVerifiedAt(verified, (BatteryReading){BatteryAbsent, -1, 0}, stamp) == nil;
    BatteryReading valid = {BatteryValid, 83, 1};
    BOOL age = PresentationReading(valid, stamp, [stamp dateByAddingTimeInterval:300]).state == BatteryValid &&
        PresentationReading(valid, stamp, [stamp dateByAddingTimeInterval:300.01]).state == BatteryUnknown &&
        PresentationReading(valid, stamp, [stamp dateByAddingTimeInterval:-1]).percent == -1 &&
        PresentationReading(valid, nil, stamp).percent == -1 &&
        PresentationReading((BatteryReading){BatteryTimedOut, -1, 0}, stamp, stamp).state == BatteryTimedOut;
    puts(age ? "PASS: sample age" : "FAIL: sample age");
    NSString *corpus = [NSProcessInfo processInfo].environment[@"AJAZZ_TEST_CORPUS"];
    BOOL pass = (!corpus || VerifyObservationCorpus(corpus)) && provenance && age && safe && shared && ParseBattery(first, 4) == 1 &&
        ParseBattery(full, 4) == 100 &&
        ParseBattery(stripped, 3) == 25 &&
        ParseBattery(zero, 4) == -1 &&
        ParseBattery(excess, 4) == -1 &&
        ParseBattery(wrongID, 4) == -1 &&
        ParseBattery(malformed, 4) == -1 &&
        ParseBattery(shortFrame, 2) == -1;
    puts(pass ? "PASS: compact and shared HID reports, unverified states"
              : "FAIL: HID parser/notification-state regression");
    return pass ? 0 : 1;
}

static int ParseTimeout(const char *value) {
    if (!value || !*value) return -1;
    char *end = NULL;
    errno = 0;
    long parsed = strtol(value, &end, 10);
    if (errno || *end != '\0' || parsed < 3 || parsed > 90) return -1;
    return (int)parsed;
}

static void Help(void) {
    puts("Usage: AJAZZBatteryTrayHighSierra "
         "[--help|--self-test|--diagnose|--trace-hid] "
         "[--timeout 3..90] [--output PATH]");
    puts("Optional: --experimental-isolated-polling (session only).");
    puts("Exit: 0 verified; 2 unknown; 124 HID timeout; 1 error.");
    puts("--output creates a private 0600 log, writes every step immediately.");
    puts("The F7/05 battery query is the only vendor feature report sent.");
}

static int RunMode(const char *mode, int timeout, NSString *output) {
    if (output && LegacyPrepareOutput(output)) return 1;
    if (!strcmp(mode, "--self-test-watchdog"))
        return LegacyRunBoundedWorker("--internal-test-sleep", 1);
    const char *worker = !strcmp(mode, "--trace-hid") ?
        "--internal-trace-hid" : "--internal-diagnose";
    int limit = timeout > 0 ? timeout :
        (!strcmp(mode, "--trace-hid") ? 20 : 15);
    return LegacyRunBoundedWorker(worker, limit);
}

int main(int argc, char *argv[]) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    @autoreleasepool {
        const char *mode = NULL;
        NSString *output = nil;
        BOOL outputRequested = NO;
        int timeout = 0;
        for (int i = 1; i < argc; i++) {
            if (!strcmp(argv[i], "--output") && i + 1 < argc &&
                !outputRequested) {
                outputRequested = YES;
                output = [NSString stringWithUTF8String:argv[++i]];
                if (!output.length) return 1;
            } else if (!strcmp(argv[i], "--timeout") && i + 1 < argc &&
                       !timeout) {
                timeout = ParseTimeout(argv[++i]);
                if (timeout < 0) break;
            } else if (!mode && (!strcmp(argv[i], "--help") ||
                       !strcmp(argv[i], "-h") ||
                       !strcmp(argv[i], "--self-test") ||
                       !strcmp(argv[i], "--diagnose") ||
                       !strcmp(argv[i], "--trace-hid") ||
                       !strcmp(argv[i], "--self-test-watchdog") ||
                       !strcmp(argv[i], "--self-test-menu-diagnostic") ||
                       !strcmp(argv[i], "--internal-trace-hid") ||
                       !strcmp(argv[i], "--internal-menu-trace") ||
                       !strcmp(argv[i], "--internal-diagnose") ||
                       !strcmp(argv[i], "--internal-poll-sample") ||
                       !strcmp(argv[i], "--internal-test-io-lease") ||
                       !strcmp(argv[i], "--experimental-isolated-polling") ||
                       !strcmp(argv[i], "--self-test-routine-poll") ||
                       !strcmp(argv[i], "--internal-routine-read") ||
                       !strcmp(argv[i], "--internal-routine-sample") ||
                       !strcmp(argv[i], "--internal-routine-hang") ||
                       !strcmp(argv[i], "--internal-test-sleep"))) {
                mode = argv[i];
            } else {
                fprintf(stderr, "FAIL: invalid arguments\n");
                return 1;
            }
        }
        if (timeout < 0 || (output && !output.length)) return 1;
        if (!mode && (output || timeout)) return 1;
        BOOL diagnostic = mode && (!strcmp(mode, "--diagnose") ||
            !strcmp(mode, "--trace-hid"));
        BOOL testWatchdog = mode && !strcmp(mode, "--self-test-watchdog");
        if ((output && !diagnostic && !testWatchdog) ||
            (timeout && !diagnostic)) {
            fputs("FAIL: unsupported diagnostic options for this mode\n", stderr);
            return 1;
        }
        BOOL isolated = mode && !strcmp(mode, "--experimental-isolated-polling");
        if (!mode || isolated) {
            NSApplication *app = [NSApplication sharedApplication];
            LegacyTray *delegate = [[LegacyTray alloc] init];
            delegate.isolatedPolling = isolated;
            app.delegate = delegate;
            [app run];
            return 0;
        }
        if (!strcmp(mode, "--help") || !strcmp(mode, "-h")) {
            Help();
            return 0;
        }
        if (!strcmp(mode, "--self-test-menu-diagnostic")) {
            NSString *trace = CaptureMenuTrace(YES, nil, 1);
            if (![trace containsString:@"INCOMPLETE: timeout;"] ||
                ![trace containsString:@"Diagnostic exit: 124"] ||
                !MenuTraceChildReaped(trace) || !AjazzDiagnosticExportSelfTest()) return 1;
            LegacyPollCancellation *cancel = [[LegacyPollCancellation alloc] init];
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 750 * NSEC_PER_MSEC),
                           dispatch_get_global_queue(QOS_CLASS_UTILITY, 0), ^{ cancel.cancelled = YES; });
            NSString *partial = CaptureMenuTrace(YES, cancel, 4);
            if (![partial containsString:@"INCOMPLETE: cancelled;"] ||
                [partial containsString:@"PASS: battery="] ||
                ([partial containsString:@"TEST: worker started; pid="] &&
                 !MenuTraceChildReaped(partial))) return 1;
            LegacyPollCancellation *before = [[LegacyPollCancellation alloc] init];
            before.cancelled = YES;
            if (![CaptureMenuTrace(YES, before, 4) containsString:@"INCOMPLETE: cancelled;"]) return 1;
            NSString *redacted = IncompleteMenuTrace(@"STEP: before read\nPASS: battery=83%\nunfinished", @"cancelled");
            if ([redacted containsString:@"83%"] || [redacted containsString:@"unfinished"] ||
                ![redacted containsString:@"STEP: before read"]) return 1;
            puts("PASS: menu capture timeout, cancellation, reaping and redaction without HID");
            return 0;
        }
        if (!strcmp(mode, "--self-test-routine-poll")) return RoutineSelfTest();
        if (!strcmp(mode, "--internal-routine-read") ||
            !strcmp(mode, "--internal-routine-sample") ||
            !strcmp(mode, "--internal-routine-hang")) return RoutineChild(mode);
        if (!strcmp(mode, "--internal-test-io-lease")) {
            int lease = AjazzAcquireIoLease();
            if (lease < 0) return 2;
            AjazzReleaseIoLease(lease);
            return 0;
        }
        if (!strcmp(mode, "--internal-poll-sample")) {
            puts("{\"kind\":\"synthetic\",\"percent\":null,\"presence\":\"unknown\"}");
            return 0;
        }
        if (!strcmp(mode, "--internal-test-sleep")) {
            printf("TEST: worker started; pid=%ld; verifying bounded watchdog\n",
                   (long)getpid());
            sleep(6);
            return 0;
        }
        // A diagnostic child must not keep I/O alive indefinitely after parent exit.
        if (!strcmp(mode, "--internal-trace-hid") ||
            !strcmp(mode, "--internal-menu-trace") ||
            !strcmp(mode, "--internal-diagnose")) {
            signal(SIGALRM, SIG_DFL);
            BOOL menu = !strcmp(mode, "--internal-menu-trace");
            alarm(menu ? 22 : 92); // abandoned child bound
            int result = menu || !strcmp(mode, "--internal-trace-hid")
                ? TraceReceiver() : DiagnoseReceiver();
            alarm(0);
            return result;
        }
        if (!strcmp(mode, "--self-test")) return SelfTest();
        return RunMode(mode, timeout, output);
    }
}
