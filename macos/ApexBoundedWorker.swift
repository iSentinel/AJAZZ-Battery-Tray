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
        case "unsupported": return .unsupportedCollection
        default: return nil
        }
    }
}

/// Prototype only. The regular menu-bar timer does not call this supervisor.
enum ApexBoundedWorker {
    static let readMode = "--internal-bounded-apex-read"
    static let sampleMode = "--internal-bounded-apex-sample"
    static let hangMode = "--internal-bounded-apex-hang"
    private static let gate = NSLock()

    enum Result: Equatable {
        case reply(ApexBattery.Status)
        case timeout
        case busy
        case failed
    }

    static func isWorker(_ mode: String) -> Bool {
        [readMode, sampleMode, hangMode].contains(mode)
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
        let value: ApexBattery.Status = mode == sampleMode ? .accessUnknown : ApexBattery.read()
        do {
            let data = try JSONEncoder().encode(ApexWorkerReply(value))
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

    /// The worker emits at most one tiny JSON object. No raw HID output.
    static func read(mode: String = readMode, timeout: Double = 8) -> Result {
        guard gate.try() else { return .busy }
        defer { gate.unlock() }
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
        if done.wait(timeout: .now() + timeout) == .timedOut {
            if child.isRunning { kill(child.processIdentifier, SIGKILL) }
            // Keep the gate until process exit is observed.
            child.waitUntilExit()
            return .timeout
        }
        child.waitUntilExit()
        guard child.terminationReason == .exit, child.terminationStatus == 0 else {
            return .failed
        }
        return decode(pipe.fileHandleForReading.readDataToEndOfFile())
    }

    static func selfTest() -> Bool {
        let states: [ApexBattery.Status] = [
            .battery(1), .battery(83), .battery(100), .notConnected,
            .unavailable, .accessUnknown, .unsupportedCollection
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
        return read(mode: sampleMode) == .reply(.accessUnknown)
    }
}
