import Foundation
import AppKit

/// Saves battery observations to a local CSV without serial numbers.
final class BatteryHistoryWriter {
    let directory: URL
    let file: URL
    private var lastValue: String?
    private var lastWrite = Date.distantPast
    private var lastPrune = Date.distantPast

    init() {
        directory = FileManager.default.urls(
            for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("AJAZZBatteryTray", isDirectory: true)
        file = directory.appendingPathComponent("battery-history.csv")
        try? FileManager.default.createDirectory(
            at: directory, withIntermediateDirectories: true)
    }

    static func shouldRecord(previous: String?, current: String,
                             secondsSinceLast: TimeInterval) -> Bool {
        previous != current || secondsSinceLast < 0 || secondsSinceLast >= 300
    }

    func record(_ status: ApexBattery.Status) {
        let value: String
        let state: String
        switch status {
        case .battery(let percent):
            value = String(percent)
            state = "online"
        case .notConnected:
            value = ""
            state = "disconnected"
        case .unavailable:
            value = ""
            state = "unavailable"
        }

        let now = Date()
        let fingerprint = value + "|" + state
        guard Self.shouldRecord(previous: lastValue, current: fingerprint,
            secondsSinceLast: now.timeIntervalSince(lastWrite)) else { return }
        guard append(time: now, value: value, state: state) else { return }
        lastValue = fingerprint
        lastWrite = now
        if now.timeIntervalSince(lastPrune) >= 86400 { prune(now) }
    }

    /// Return false on a disk error so the next poll retries the sample.
    private func append(time: Date, value: String, state: String) -> Bool {
        let timestamp = ISO8601DateFormatter().string(from: time)
        let row = "\(timestamp),\(value),\(state)\n"
        do {
            if !FileManager.default.fileExists(atPath: file.path) {
                try "utc_timestamp,percent,state\n".write(
                    to: file, atomically: true, encoding: .utf8)
            }
            let handle = try FileHandle(forWritingTo: file)
            defer { try? handle.close() }
            _ = try handle.seekToEnd()
            try handle.write(contentsOf: Data(row.utf8))
            return true
        } catch {
            return false
        }
    }

    private func prune(_ now: Date) {
        guard let text = try? String(contentsOf: file, encoding: .utf8) else {
            return
        }
        let parser = ISO8601DateFormatter()
        let cutoff = now.addingTimeInterval(-30 * 86400)
        let entries = text.split(separator: "\n").dropFirst().filter { row in
            guard let stamp = row.split(separator: ",").first,
                  let date = parser.date(from: String(stamp)) else { return false }
            return date >= cutoff && date <= now
        }
        let bounded = entries.suffix(20000)
        let result = "utc_timestamp,percent,state\n" +
            bounded.joined(separator: "\n") + "\n"
        do {
            try result.write(to: file, atomically: true, encoding: .utf8)
            lastPrune = now
        } catch {
            // Retain the previous history and retry pruning on the next poll.
        }
    }
}
