import Foundation
import UserNotifications

/// User-visible battery events, separate from HID communication.
enum BatteryAlertEvent: Equatable {
    case lowBattery(Int)
    case receiverDisconnected
}

/// Debounces disconnects and suppresses repeated low-battery alerts.
final class BatteryAlertPolicy {
    private var reachedThreshold: Int?
    private var observedConnection = false
    private var consecutiveMissing = 0
    private var disconnectNotified = false

    /// Returns a new event, or nil when nothing needs user attention.
    func evaluate(_ status: ApexBattery.Status,
                  notifyLow: Bool, notifyDisconnect: Bool) -> BatteryAlertEvent? {
        switch status {
        case .battery(let percent):
            observedConnection = true
            consecutiveMissing = 0
            disconnectNotified = false
            if percent > 25 { reachedThreshold = nil }
            guard notifyLow else { return nil }
            let threshold: Int?
            switch percent {
            case ...5: threshold = 5
            case ...10: threshold = 10
            case ...20: threshold = 20
            default: threshold = nil
            }
            guard let threshold = threshold else { return nil }
            if let previous = reachedThreshold, threshold >= previous {
                return nil
            }
            reachedThreshold = threshold
            return .lowBattery(percent)

        case .unavailable:
            // Sleeping mouse, but USB receiver remains connected.
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
                content.title = "AJAZZ APEX: low battery"
                content.body = "Mouse battery is at \(level)%."
            case .receiverDisconnected:
                content.title = "AJAZZ APEX: receiver disconnected"
                content.body = "The 2.4 GHz / 8K receiver is no longer detected."
            }
            content.sound = .default
            let request = UNNotificationRequest(
                identifier: UUID().uuidString, content: content, trigger: nil)
            center.add(request) { _ in }
        }
    }
}
