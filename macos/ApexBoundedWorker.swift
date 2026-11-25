import Foundation
import Darwin

/// Local IPC representation; only verified battery frames may carry a percentage.
struct ApexWorkerReply: Codable {
    let state: String
    let percent: Int?

    init(_ status: ApexBattery.Status) {
        switch status {
        case .battery(let value): state = "battery"; percent = value
        case .notConnected: state = "absent"; percent = nil
        case .unavailable: state = "unavailable"; percent = nil
        case .accessUnknown: state = "unknown"; percent = nil
        case .timedOut: state = "timeout"; percent = nil
        case .unsupportedCollection: state = "unsupported"; percent = nil
        }
    }

    var status: ApexBattery.Status? {
        if state == "battery", let value = percent, (1...100).contains(value) {
            return .battery(value)
        }
        guard percent == nil else { return nil }
        switch state {
        case "absent": return .notConnected
        case "unavailable": return .unavailable
        case "unknown": return .accessUnknown
        case "timeout": return .timedOut
        case "unsupported": return .unsupportedCollection
        default: return nil
        }
    }
}

/// Thread-safe cancellation flag; only the supervisor signals its child.
final class ApexWorkerCancellation {
    private let lock = NSLock()
    private var cancelled = false

    func cancel() {
        lock.lock()
        cancelled = true
        lock.unlock()
    }

    var isCancelled: Bool {
        lock.lock()
        defer { lock.unlock() }
        return cancelled
    }
}

/// Supervisor for the explicit experimental menu mode.
enum ApexBoundedWorker {
    static let traceMode = "--internal-bounded-apex-trace"
    static let traceSampleMode = "--internal-bounded-apex-trace-sample"
    static let readMode = "--internal-bounded-apex-read"
    static let sampleMode = "--internal-bounded-apex-sample"
    static let hangMode = "--internal-bounded-apex-hang"
    static let clockMode = "--internal-bounded-apex-clock"
    static let clockSampleMode = "--internal-bounded-apex-clock-sample"
    private static let gate = NSLock()

    enum Result: Equatable {
        case trace(String)
        case reply(ApexBattery.Status)
        case clock(Bool)
        case timeout
        case cancelled
        case busy
        case failed
    }

    static func isWorker(_ mode: String) -> Bool {
        [readMode, sampleMode, hangMode, clockMode, clockSampleMode, traceMode, traceSampleMode].contains(mode)
    }

    static func runChild(_ mode: String) -> Int32 {
        // Also bound an abandoned child after its supervising process exits.
        signal(SIGALRM, SIG_DFL)
        alarm(12)
        defer { alarm(0) }
        if mode == hangMode {
            sleep(30)
            return 1
        }
        do {
            let data: Data
            if mode == traceMode || mode == traceSampleMode {
                var lines = [String]()
                let value: ApexBattery.Status = mode == traceSampleMode ? .accessUnknown : ApexBattery.read {
                    if lines.count < 16 { lines.append($0) }
                }
                lines.append("Battery status: " + ApexWorkerReply(value).state)
                if case .battery(let level) = value { lines.append("Verified battery: \(level)%") }
                data = try JSONEncoder().encode(lines.joined(separator: "\n"))
            } else if mode == clockMode || mode == clockSampleMode {
                data = try JSONEncoder().encode(mode == clockSampleMode || ApexBattery.syncClock())
            } else {
                let value: ApexBattery.Status = mode == sampleMode ? .accessUnknown : ApexBattery.read()
                data = try JSONEncoder().encode(ApexWorkerReply(value))
            }
            FileHandle.standardOutput.write(data)
            return 0
        } catch { return 1 }
    }

    static func decode(_ data: Data) -> Result {
        guard data.count <= 1024,
              let reply = try? JSONDecoder().decode(ApexWorkerReply.self, from: data),
              let status = reply.status else { return .failed }
        return .reply(status)
    }

    /// Routine IPC has no vendor bytes; explicit trace is capped to a small JSON string.
    static func read(mode: String = readMode, timeout: Double = 8,
                     cancellation: ApexWorkerCancellation? = nil) -> Result {
        guard cancellation?.isCancelled != true else { return .cancelled }
        guard gate.try() else { return .busy }
        defer { gate.unlock() }
        guard cancellation?.isCancelled != true else { return .cancelled }
        guard let path = Bundle.main.executablePath else { return .failed }
        let child = Process()
        let pipe = Pipe()
        let done = DispatchSemaphore(value: 0)
        child.executableURL = URL(fileURLWithPath: path)
        child.arguments = [mode]
        child.standardOutput = pipe
        child.standardError = FileHandle.nullDevice
        child.terminationHandler = { _ in done.signal() }
        do { try child.run() } catch { return .failed }
        try? pipe.fileHandleForWriting.close()
        let deadline = DispatchTime.now() + timeout
        while true {
            if cancellation?.isCancelled == true {
                stopAndWait(child)
                return .cancelled
            }
            let next = min(deadline, DispatchTime.now() + .milliseconds(50))
            if done.wait(timeout: next) == .success { break }
            if DispatchTime.now() >= deadline {
                stopAndWait(child)
                return .timeout
            }
        }
        child.waitUntilExit()
        guard cancellation?.isCancelled != true else { return .cancelled }
        guard child.terminationReason == .exit, child.terminationStatus == 0 else {
            return .failed
        }
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        if mode == traceMode || mode == traceSampleMode {
            guard data.count <= 4096, let text = try? JSONDecoder().decode(String.self, from: data)
            else { return .failed }
            return .trace(text)
        }
        if mode == clockMode || mode == clockSampleMode {
            guard data.count <= 1024,
                  let sent = try? JSONDecoder().decode(Bool.self, from: data)
            else { return .failed }
            return .clock(sent)
        }
        return decode(data)
    }

    private static func stopAndWait(_ child: Process) {
        if child.isRunning { kill(child.processIdentifier, SIGKILL) }
        // Keep the gate until process exit is observed.
        child.waitUntilExit()
    }

    static func selfTest() -> Bool {
        let states: [ApexBattery.Status] = [
            .battery(1), .battery(83), .battery(100), .notConnected,
            .unavailable, .accessUnknown, .unsupportedCollection, .timedOut
        ]
        for status in states {
            guard let data = try? JSONEncoder().encode(ApexWorkerReply(status)),
                  decode(data) == .reply(status) else { return false }
        }
        let invalid = [
            "{\"state\":\"battery\",\"percent\":0}",
            "{\"state\":\"battery\",\"percent\":101}",
            "{\"state\":\"absent\",\"percent\":83}",
            "{\"state\":\"unknown\",\"percent\":25}",
            "{\"state\":\"battery\"}", "{\"state\":\"other\"}", "broken"
        ]
        guard invalid.allSatisfy({ decode(Data($0.utf8)) == .failed }) else { return false }
        gate.lock()
        let busy = read(mode: sampleMode)
        gate.unlock()
        guard busy == .busy else { return false }
        guard read(mode: sampleMode) == .reply(.accessUnknown) else { return false }
        guard read(mode: hangMode, timeout: 1) == .timeout else { return false }

        let alreadyCancelled = ApexWorkerCancellation()
        alreadyCancelled.cancel()
        guard read(mode: sampleMode, cancellation: alreadyCancelled) == .cancelled
        else { return false }

        let during = ApexWorkerCancellation()
        DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(250)) {
            during.cancel()
        }
        guard read(mode: hangMode, timeout: 4, cancellation: during) == .cancelled
        else { return false }
        guard read(mode: traceSampleMode) == .trace("Battery status: unknown") else { return false }
        return read(mode: sampleMode) == .reply(.accessUnknown) &&
            read(mode: clockSampleMode) == .clock(true)
    }
}
