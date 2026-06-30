import SwiftUI

/// Markenfarben -- identisch zu den Hex-Werten in awtrix.py, damit Uhr und
/// Widget gleich aussehen.
enum Theme {
    static let igPink      = Color(hex: 0xE1306C)   // Instagram
    static let mailBlue    = Color(hex: 0x4AA3FF)
    static let homeLime    = Color(hex: 0xA6E22E)   // Homepage / Ziel
    static let revenueGreen = Color(hex: 0x39FF14)  // Einnahmen
    static let growthGreen = Color(hex: 0x2ECC40)   // Tageszuwachs
    static let dropRed     = Color(hex: 0xFF4136)   // Rueckgang
    static let cardBG      = Color(hex: 0x0E0E12)
    static let subtle      = Color.white.opacity(0.55)

    /// Gruen bei >= 0, rot bei < 0 -- wie die Faerbung auf der Uhr.
    static func delta(_ value: Double?) -> Color {
        guard let value else { return subtle }
        return value >= 0 ? growthGreen : dropRed
    }
}

extension Color {
    init(hex: UInt32) {
        self.init(
            .sRGB,
            red:   Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue:  Double(hex & 0xFF) / 255,
            opacity: 1
        )
    }
}
