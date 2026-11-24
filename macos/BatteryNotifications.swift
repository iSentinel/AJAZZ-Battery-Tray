import Foundation
import UserNotifications

/// User-visible battery events, separate from HID communication.
enum BatteryAlertEvent: Equatable {
    case lowBattery(Int)
    case receiverDisconnected
}

/// Debounces disconnects and suppresses repeated low-battery alerts.
final class BatteryAlertPolicy {
    private var notifiedThresholds = Set<Int>()
    private var observedConnection = false
    private var consecutiveMissing = 0
    private var disconnectNotified = false

    /// Returns a new event at enabled strictly-below battery thresholds.
    func evaluate(_ status: ApexBattery.Status,
                  notifyLow: Bool, notifyDisconnect: Bool,
                  thresholds: Set<Int> = [50, 25, 10]) -> BatteryAlertEvent? {
        switch status {
        case .battery(let percent):
            observedConnection = true
            consecutiveMissing = 0
            disconnectNotified = false
            // Five percent of hysteresis avoids repeated threshold warnings.
            for threshold in [50, 25, 10] where percent >= threshold + 5 {
                notifiedThresholds.remove(threshold)
            }
            guard notifyLow else { return nil }
            let reached = [10, 25, 50].first {
                thresholds.contains($0) && percent < $0 &&
                    !notifiedThresholds.contains($0)
            }
            guard reached != nil else { return nil }
            // A large drop should emit one most-urgent warning.
            for threshold in [50, 25, 10] where percent < threshold {
                notifiedThresholds.insert(threshold)
            }
            return .lowBattery(percent)

        case .unavailable, .accessUnknown, .unsupportedCollection, .timedOut:
            // Only consecutive confirmed absences can trigger a disconnect.
            consecutiveMissing = 0
            return nil

        case .notConnected:
            consecutiveMissing += 1
            guard notifyDisconnect, observedConnection,
                  !disconnectNotified, consecutiveMissing >= 2 else {
                return nil
            }
            disconnectNotified = true
            return .receiverDisconnected
        }
    }
}

/// Requests permission only after a user enables alerts from the menu.
enum BatteryLocalNotifications {
    static func requestPermission() {
        UNUserNotificationCenter.current().requestAuthorization(
            options: [.alert, .sound]) { _, _ in
                // A refusal is respected: notification delivery checks authorization.
            }
    }

    static func deliver(_ event: BatteryAlertEvent) {
        let center = UNUserNotificationCenter.current()
        center.getNotificationSettings { settings in
            guard settings.authorizationStatus == .authorized ||
                  settings.authorizationStatus == .provisional else {
                return
            }

            let content = UNMutableNotificationContent()
            switch event {
            case .lowBattery(let level):
                content.title = AppText.text("AJAZZ APEX: low battery")
                content.body = AppText.format("Mouse battery is at %d%%.", level)
            case .receiverDisconnected:
                content.title = AppText.text("AJAZZ APEX: receiver disconnected")
                content.body = AppText.text(
                    "The 2.4 GHz / 8K receiver is no longer detected.")
            }
            content.sound = .default
            let request = UNNotificationRequest(
                identifier: UUID().uuidString, content: content, trigger: nil)
            center.add(request) { _ in }
        }
    }
}
