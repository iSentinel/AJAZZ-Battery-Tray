import AppKit

/// Appearance only; never changes a battery observation or notification policy.
enum TrayAppearance {
    static let choices = ["orange", "white", "black", "blue"]

    static func choice(_ key: String) -> String {
        let value = UserDefaults.standard.string(forKey: key) ?? "orange"
        return choices.contains(value) ? value : "orange"
    }

    static func mouseStyle() -> Bool {
        UserDefaults.standard.object(forKey: "MouseTrayIcon") == nil ||
            UserDefaults.standard.bool(forKey: "MouseTrayIcon")
    }

    static func appIcon(_ color: String) -> NSImage? {
        let file = color == "orange" ? "AppIcon" : "AppIcon-" + color
        guard choices.contains(color),
              let url = Bundle.main.url(forResource: file, withExtension: "icns") else { return nil }
        return NSImage(contentsOf: url)
    }

    static func color(_ choice: String, _ level: Int?) -> NSColor {
        guard let level = level, (0...100).contains(level) else { return .systemGray }
        if level <= 10 { return NSColor(srgbRed: 0.86, green: 0.21, blue: 0.27, alpha: 1) }
        if level <= 20 { return NSColor(srgbRed: 0.88, green: 0.57, blue: 0.07, alpha: 1) }
        switch choice {
        case "white": return NSColor(white: 0.95, alpha: 1)
        case "black": return NSColor(white: 0.13, alpha: 1)
        case "blue": return NSColor(srgbRed: 0.14, green: 0.39, blue: 0.78, alpha: 1)
        default: return NSColor(srgbRed: 0.96, green: 0.47, blue: 0.09, alpha: 1)
        }
    }

    static func image(level: Int?, choice: String, mouseStyle: Bool) -> NSImage {
        let valid = level.flatMap { (0...100).contains($0) ? $0 : nil }
        let mouse = mouseStyle && (valid ?? 0) > 20
        let size = NSSize(width: mouse ? 18 : 36, height: 18)
        let background = color(choice, valid)
        let image = NSImage(size: size, flipped: false) { rect in
            let body = NSBezierPath(roundedRect: rect.insetBy(dx: mouse ? 3 : 1, dy: 1),
                                    xRadius: mouse ? 6 : 5, yRadius: mouse ? 6 : 5)
            background.setFill()
            body.fill()
            NSColor(white: 0.65, alpha: 1).setStroke()
            body.lineWidth = 0.8
            body.stroke()
            if mouse {
                NSColor.darkGray.setStroke()
                let seams = NSBezierPath()
                seams.move(to: NSPoint(x: 9, y: 16))
                seams.line(to: NSPoint(x: 9, y: 10))
                seams.move(to: NSPoint(x: 3, y: 10))
                seams.line(to: NSPoint(x: 15, y: 10))
                seams.lineWidth = 1
                seams.stroke()
            } else {
                let text = valid.map { "\($0)%" } ?? "?"
                let paragraph = NSMutableParagraphStyle()
                paragraph.alignment = .center
                let darkText = choice == "white" && (valid ?? 0) > 20
                (text as NSString).draw(in: NSRect(x: 0, y: 2, width: size.width, height: 15),
                    withAttributes: [.font: NSFont.boldSystemFont(ofSize: 11),
                                     .foregroundColor: darkText ? NSColor.black : NSColor.white,
                                     .paragraphStyle: paragraph])
            }
            return true
        }
        image.isTemplate = false
        return image
    }

    static func selfTest() -> Bool {
        for choice in choices {
            guard let asset = appIcon(choice), asset.isValid else { return false }
            for level in [0, 8, 10, 11, 20, 21, 100, -1, 101] {
                let rendered = image(level: level, choice: choice, mouseStyle: true)
                let expectedWidth: CGFloat = level > 20 && level <= 100 ? 18 : 36
                guard rendered.size == NSSize(width: expectedWidth, height: 18),
                      !rendered.isTemplate, let bytes = rendered.tiffRepresentation,
                      let bitmap = NSBitmapImageRep(data: bytes) else { return false }
                if level >= 0 && level <= 10 && !hasRed(bitmap) { return false }
                if (level < 0 || level > 10) && hasRed(bitmap) { return false }
            }
        }
        return appIcon("../invalid") == nil
    }

    private static func hasRed(_ bitmap: NSBitmapImageRep) -> Bool {
        for x in 0..<bitmap.pixelsWide {
            for y in 0..<bitmap.pixelsHigh {
                guard let pixel = bitmap.colorAt(x: x, y: y)?.usingColorSpace(.deviceRGB)
                else { continue }
                if pixel.alphaComponent > 0.8 && pixel.redComponent > 0.75 &&
                    pixel.greenComponent < 0.35 && pixel.blueComponent < 0.4 { return true }
            }
        }
        return false
    }
}
