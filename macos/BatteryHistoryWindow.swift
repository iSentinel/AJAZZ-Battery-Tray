import AppKit
import Foundation

/// A local observation; nil charge means disconnected or unavailable.
struct BatteryObservation {
    let timestamp: Date
    let percent: Int?
    let state: String
}

/// Parses saved CSV. No USB access is performed when opening the chart.
enum BatteryHistoryReader {
    static func parse(_ row: String) -> BatteryObservation? {
        let fields = row.split(separator: ",", omittingEmptySubsequences: false)
        guard fields.count == 3 else { return nil }

        let parser = ISO8601DateFormatter()
        guard let time = parser.date(from: String(fields[0])) else { return nil }
        let state = String(fields[2])
        guard ["online", "unavailable", "disconnected"].contains(state) else {
            return nil
        }

        let charge = Int(fields[1])
        if state == "online" {
            guard let value = charge, (1...100).contains(value) else {
                return nil
            }
        } else if !fields[1].isEmpty {
            return nil
        }
        return BatteryObservation(timestamp: time, percent: charge, state: state)
    }

    static func load(_ file: URL, from start: Date, through end: Date)
        -> [BatteryObservation] {
        guard let csv = try? String(contentsOf: file, encoding: .utf8) else {
            return []
        }

        return csv.split(separator: "\n").dropFirst()
            .compactMap { parse(String($0)) }
            .filter { $0.timestamp >= start && $0.timestamp <= end }
            .sorted { $0.timestamp < $1.timestamp }
            .suffix(20_000).map { $0 }
    }
}

/// Percentage-over-time chart. Gaps are never interpreted as 0% charge.
final class BatteryHistoryChart: NSView {
    var samples = [BatteryObservation]() { didSet { needsDisplay = true } }
    var periodStart = Date().addingTimeInterval(-86_400)
    var periodEnd = Date()

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)
        NSColor.windowBackgroundColor.setFill()
        NSRectFill(bounds)
        let plot = NSRect(x: 57, y: 45, width: max(1, bounds.width - 83),
                          height: max(1, bounds.height - 70))
        drawGrid(plot)
        drawSeries(plot)
    }

    private func drawGrid(_ plot: NSRect) {
        let style: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 10),
            .foregroundColor: NSColor.secondaryLabelColor
        ]

        NSColor.separatorColor.setStroke()
        for level in stride(from: 0, through: 100, by: 25) {
            let y = plot.minY + CGFloat(level) / 100 * plot.height
            let path = NSBezierPath()
            path.move(to: NSPoint(x: plot.minX, y: y))
            path.line(to: NSPoint(x: plot.maxX, y: y))
            path.stroke()
            ("\(level)%" as NSString).draw(
                at: NSPoint(x: 13, y: y - 6), withAttributes: style)
        }

        let formatter = DateFormatter()
        formatter.dateFormat = "dd MMM HH:mm"
        let span = max(1, periodEnd.timeIntervalSince(periodStart))
        for step in 0...4 {
            let fraction = Double(step) / 4
            let instant = periodStart.addingTimeInterval(span * fraction)
            let x = plot.minX + CGFloat(fraction) * plot.width
            (formatter.string(from: instant) as NSString).draw(
                at: NSPoint(x: x - 37, y: plot.minY - 24),
                withAttributes: style)
        }
    }

    private func drawSeries(_ plot: NSRect) {
        if samples.isEmpty {
            let style: [NSAttributedString.Key: Any] = [
                .font: NSFont.systemFont(ofSize: 13),
                .foregroundColor: NSColor.secondaryLabelColor
            ]
            ("No observations for the selected period" as NSString).draw(
                at: NSPoint(x: plot.minX + 12, y: plot.midY),
                withAttributes: style)
            return
        }

        let span = max(1, periodEnd.timeIntervalSince(periodStart))
        var previous: (point: NSPoint, time: Date)?
        for sample in samples {
            guard let percent = sample.percent else {
                previous = nil
                continue
            }

            let fraction = sample.timestamp.timeIntervalSince(periodStart) / span
            let point = NSPoint(x: plot.minX + CGFloat(fraction) * plot.width,
                                y: plot.minY + CGFloat(percent) / 100 * plot.height)
            if let last = previous,
               sample.timestamp.timeIntervalSince(last.time) <= 1_800 {
                let path = NSBezierPath()
                path.lineWidth = 2.5
                path.move(to: last.point)
                path.line(to: point)
                NSColor.systemGreen.setStroke()
                path.stroke()
            }

            NSColor.systemGreen.setFill()
            NSBezierPath(ovalIn: NSRect(x: point.x - 2, y: point.y - 2,
                                      width: 4, height: 4)).fill()
            previous = (point, sample.timestamp)
        }
    }
}

/// A simple native history window with 24h, 7d and 30d selections.
final class BatteryHistoryWindowController: NSWindowController {
    private let file: URL
    private let plot = BatteryHistoryChart()
    private let range = NSPopUpButton()
    private let status = NSTextField(labelWithString: "")

    init(file: URL) {
        self.file = file
        let frame = NSRect(x: 0, y: 0, width: 860, height: 490)
        let window = NSWindow(contentRect: frame,
                              styleMask: [.titled, .closable, .resizable, .miniaturizable],
                              backing: .buffered, defer: false)
        window.title = "AJAZZ APEX — Battery history"
        window.minSize = NSSize(width: 660, height: 370)
        window.isReleasedWhenClosed = false
        super.init(window: window)
        configure()
        refresh()
    }

    required init?(coder: NSCoder) {
        fatalError("Create the controller with a history file")
    }

    private func configure() {
        guard let root = window?.contentView else { return }
        range.frame = NSRect(x: 16, y: root.bounds.height - 45,
                             width: 164, height: 28)
        range.addItems(withTitles: ["Last 24 hours", "Last 7 days", "Last 30 days"])
        range.selectItem(at: 1)
        range.target = self
        range.action = #selector(refresh)
        range.autoresizingMask = [.minYMargin]
        root.addSubview(range)

        let reload = NSButton(title: "Refresh", target: self,
                              action: #selector(refresh))
        reload.frame = NSRect(x: 186, y: root.bounds.height - 44,
                              width: 90, height: 27)
        reload.autoresizingMask = [.minYMargin]
        root.addSubview(reload)

        let folder = NSButton(title: "Open CSV folder", target: self,
                              action: #selector(openFolder))
        folder.frame = NSRect(x: 284, y: root.bounds.height - 44,
                              width: 146, height: 27)
        folder.autoresizingMask = [.minYMargin]
        root.addSubview(folder)

        plot.frame = NSRect(x: 10, y: 57, width: root.bounds.width - 20,
                            height: root.bounds.height - 113)
        plot.autoresizingMask = [.width, .height]
        root.addSubview(plot)

        status.frame = NSRect(x: 18, y: 15, width: root.bounds.width - 36,
                              height: 32)
        status.font = NSFont.systemFont(ofSize: 11)
        status.textColor = .secondaryLabelColor
        status.autoresizingMask = [.width]
        root.addSubview(status)
    }

    @objc func refresh() {
        let days: Double = range.indexOfSelectedItem == 0 ? 1 :
                           range.indexOfSelectedItem == 1 ? 7 : 30
        let end = Date()
        let start = end.addingTimeInterval(-days * 86_400)
        let points = BatteryHistoryReader.load(file, from: start, through: end)
        plot.periodStart = start
        plot.periodEnd = end
        plot.samples = points

        let last = points.last
        let value = last?.percent.map { "\($0)%" } ?? last?.state ?? "no data"
        let minimum = points.compactMap { $0.percent }.min().map { "\($0)%" } ?? "—"
        let absent = points.filter { $0.state == "disconnected" }.count
        status.stringValue = "Latest: \(value)  •  Minimum: \(minimum)" +
            "  •  Receiver absent: \(absent)  •  \(points.count) observations"
    }

    @objc private func openFolder() {
        NSWorkspace.shared.open(file.deletingLastPathComponent())
    }
}
