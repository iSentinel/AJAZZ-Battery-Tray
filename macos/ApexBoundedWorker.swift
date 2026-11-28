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
    static let traceHangMode = "--internal-bounded-apex-trace-hang"
    static let traceFailMode = "--internal-bounded-apex-trace-fail"
    static let readMode = "--internal-bounded-apex-read"
    static let sampleMode = "--internal-bounded-apex-sample"
    static let hangMode = "--internal-bounded-apex-hang"
    static let clockMode = "--internal-bounded-apex-clock"
    static let clockSampleMode = "--internal-bounded-apex-clock-sample"
    private static let gate = NSLock()

    enum Result: Equatable {
        case trace(String)
        case partialTrace(String, String)
        case reply(ApexBattery.Status)
        case clock(Bool)
        case timeout
        case cancelled
        case busy
        case failed
    }

    /// Preserve supervisor provenance separately from the existing battery UI mapping.
    static func routineOutcome(_ result: Result) -> (ApexBattery.Status, AjazzRoutineOutcome) {
        switch result {
        case .reply(let status): return (status, AjazzRoutineReply)
        case .timeout: return (.timedOut, AjazzRoutineTimeout)
        case .cancelled: return (.accessUnknown, AjazzRoutineCancelled)
        case .busy: return (.accessUnknown, AjazzRoutineBusy)
        default: return (.accessUnknown, AjazzRoutineFailed)
        }
    }

    static func isWorker(_ mode: String) -> Bool {
        [readMode, sampleMode, hangMode, clockMode, clockSampleMode].contains(mode) || isTrace(mode)
    }

    private static func isTrace(_ mode: String) -> Bool {
        [traceMode, traceSampleMode, traceHangMode, traceFailMode].contains(mode)
    }

    /// Fixed, short, newline-terminated records are immediately visible to the parent.
    private static func emitTraceLine(_ line: String) {
        guard line.utf8.count <= 192, !line.contains("\n"), !line.contains("\r") else { return }
        FileHandle.standardOutput.write(Data((line + "\n").utf8))
    }

    private static func runTrace(_ mode: String) -> Int32 {
        if mode == traceHangMode || mode == traceFailMode {
            emitTraceLine("STEP: synthetic trace checkpoint")
            FileHandle.standardOutput.write(Data("unfinished".utf8))
            if mode == traceHangMode { sleep(30) }
            return 1
        }
        var count = 0
        var truncated = false
        let value: ApexBattery.Status = mode == traceSampleMode ? .accessUnknown : ApexBattery.read {
            if count < 16 {
                emitTraceLine($0)
                count += 1
            } else { truncated = true }
        }
        if truncated { emitTraceLine("Trace detail capped") }
        emitTraceLine("Battery status: " + ApexWorkerReply(value).state)
        if case .battery(let level) = value { emitTraceLine("Verified battery: \(level)%") }
        emitTraceLine("END: trace complete")
        return 0
    }

    /// On abnormal termination only complete, non-terminal records survive.
    static func traceResult(_ data: Data, failure: String?) -> Result {
        guard data.count <= 4096 else { return .failed }
        let records = data.split(separator: 10, omittingEmptySubsequences: false)
        let complete = records.dropLast()
        let lines = complete.compactMap { record -> String? in
            guard !record.isEmpty, record.count <= 192 else { return nil }
            return String(data: Data(record), encoding: .utf8)
        }
        guard complete.count == lines.count else { return .failed }
        if let failure = failure {
            let partial = lines.filter {
                !$0.hasPrefix("Battery status:") &&
                !$0.hasPrefix("Verified battery:") && $0 != "END: trace complete"
            }
            return .partialTrace(failure, partial.joined(separator: "\n"))
        }
        guard data.last == 10, lines.last == "END: trace complete",
              lines.dropLast().contains(where: { $0.hasPrefix("Battery status:") })
        else { return .failed }
        return .trace(lines.dropLast().joined(separator: "\n"))
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
            if isTrace(mode) { return runTrace(mode) }
            if mode == clockMode || mode == clockSampleMode {
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

    /// Trace records stay below 4096 bytes (including terminal records); read after reaping.
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
                return isTrace(mode) ? traceResult(pipe.fileHandleForReading.readDataToEndOfFile(), failure: "cancelled") : .cancelled
            }
            let next = min(deadline, DispatchTime.now() + .milliseconds(50))
            if done.wait(timeout: next) == .success { break }
            if DispatchTime.now() >= deadline {
                stopAndWait(child)
                return isTrace(mode) ? traceResult(pipe.fileHandleForReading.readDataToEndOfFile(), failure: "timeout") : .timeout
            }
        }
        child.waitUntilExit()
        if isTrace(mode) {
            let failure = cancellation?.isCancelled == true ? "cancelled" :
                (child.terminationReason == .exit && child.terminationStatus == 0 ? nil : "worker failed")
            return traceResult(pipe.fileHandleForReading.readDataToEndOfFile(), failure: failure)
        }
        guard cancellation?.isCancelled != true else { return .cancelled }
        guard child.terminationReason == .exit, child.terminationStatus == 0 else {
            return .failed
        }
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
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
        guard routineOutcome(.reply(.accessUnknown)).1 == AjazzRoutineReply,
              routineOutcome(.reply(.notConnected)).1 == AjazzRoutineReply,
              routineOutcome(.timeout).1 == AjazzRoutineTimeout,
              routineOutcome(.cancelled).1 == AjazzRoutineCancelled,
              routineOutcome(.busy).1 == AjazzRoutineBusy,
              routineOutcome(.failed).1 == AjazzRoutineFailed,
              routineOutcome(.failed).0 == .accessUnknown,
              routineOutcome(.timeout).0 == .timedOut else { return false }
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
        guard read(mode: traceSampleMode) == .trace("Battery status: unknown"),
              read(mode: traceHangMode, timeout: 3) == .partialTrace("timeout", "STEP: synthetic trace checkpoint"),
              read(mode: traceFailMode) == .partialTrace("worker failed", "STEP: synthetic trace checkpoint")
        else { return false }
        let traceCancellation = ApexWorkerCancellation()
        DispatchQueue.global().asyncAfter(deadline: .now() + .milliseconds(750)) {
            traceCancellation.cancel()
        }
        let cancelledTrace = read(mode: traceHangMode, timeout: 4, cancellation: traceCancellation)
        guard cancelledTrace == .partialTrace("cancelled", "STEP: synthetic trace checkpoint") ||
              cancelledTrace == .partialTrace("cancelled", "") || cancelledTrace == .cancelled
        else { return false }
        let terminal = Data("STEP: before read\nBattery status: battery\nVerified battery: 83%\nEND: trace complete\n".utf8)
        guard traceResult(terminal, failure: "timeout") == .partialTrace("timeout", "STEP: before read"),
              traceResult(Data("Battery status: unknown\n".utf8), failure: nil) == .failed,
              traceResult(Data(repeating: 65, count: 4097), failure: "timeout") == .failed
        else { return false }
        return read(mode: sampleMode) == .reply(.accessUnknown) &&
            read(mode: clockSampleMode) == .clock(true)
    }
}
