import Foundation
import Darwin

/// Saves battery observations to a local CSV without serial numbers.
final class BatteryHistoryWriter {
    let directory: URL
    let file: URL
    private var lastValue: String?
    private var lastWrite = Date.distantPast
    private var lastPrune = Date.distantPast

    init(directory override: URL? = nil) {
        directory = override ?? FileManager.default.urls(
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

    func record(_ status: ApexBattery.Status, at now: Date = Date()) {
        let value: String
        let state: String
        switch status {
        case .battery(let percent):
            value = String(percent)
            state = "online"
        case .notConnected:
            value = ""
            state = "disconnected"
        case .unavailable, .accessUnknown, .unsupportedCollection, .timedOut:
            value = ""
            state = "unavailable"
        }

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
        // The CSV has whole-second precision. Never serialize a future timestamp
        // when the formatter rounds a fractional instant across a second boundary.
        let timestamp = ISO8601DateFormatter().string(from:
            Date(timeIntervalSince1970: floor(time.timeIntervalSince1970)))
        let row = "\(timestamp),\(value),\(state)\n"
        do {
            let fd = open(file.path, O_RDWR | O_CREAT | O_APPEND, 0o600)
            guard fd >= 0 else { return false }
            let handle = FileHandle(fileDescriptor: fd, closeOnDealloc: true)
            defer { try? handle.close() }
            let size = try handle.seekToEnd()
            var prefix = ""
            if size == 0 {
                prefix = "utc_timestamp,percent,state\n"
            } else {
                try handle.seek(toOffset: size - 1)
                let last = try handle.read(upToCount: 1)?.first
                if last != 10 && last != 13 { prefix = "\n" }
            }
            try handle.write(contentsOf: Data((prefix + row).utf8))
            return true
        } catch {
            return false
        }
    }

    private func prune(_ now: Date) {
        guard let text = try? String(contentsOf: file, encoding: .utf8) else {
            return
        }
        let cutoff = now.addingTimeInterval(-30 * 86400)
        let decoder = HistoryRowDecoder()
        let entries = text.split(whereSeparator: \.isNewline).filter { row in
            guard let observation = decoder.parse(String(row)) else {
                return false
            }
            return observation.timestamp >= cutoff &&
                   observation.timestamp <= now
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
