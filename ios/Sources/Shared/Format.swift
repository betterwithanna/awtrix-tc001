import Foundation

/// Zahlen-/Datumsformatierung im selben Stil wie auf der Uhr (deutsche
/// Tausenderpunkte, signierte Deltas, kurzes ETA-Datum).
enum Format {
    private static let grouping: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .decimal
        f.groupingSeparator = "."
        f.maximumFractionDigits = 0
        return f
    }()

    /// 84210 -> "84.210"
    static func int(_ value: Double?) -> String {
        guard let value else { return "—" }
        return grouping.string(from: NSNumber(value: value.rounded())) ?? "—"
    }

    /// Tageszuwachs mit Vorzeichen: 123 -> "+123", -4 -> "-4"
    static func signedInt(_ value: Double?) -> String? {
        guard let value else { return nil }
        let rounded = value.rounded()
        let sign = rounded >= 0 ? "+" : "-"
        return sign + int(abs(rounded))
    }

    /// Prozent mit Vorzeichen und einer Nachkommastelle: 2.4 -> "+2.4%"
    static func signedPct(_ value: Double?) -> String? {
        guard let value else { return nil }
        return String(format: "%+.1f%%", value)
    }

    /// EUR-Betrag: 248.5 -> "248,50 EUR" (zwei Stellen) bzw. 7421 -> "7.421 EUR"
    static func money(_ value: Double?, sign: String, decimals: Bool = false) -> String {
        guard let value else { return "—" }
        if decimals {
            let f = NumberFormatter()
            f.numberStyle = .decimal
            f.groupingSeparator = "."
            f.decimalSeparator = ","
            f.minimumFractionDigits = 2
            f.maximumFractionDigits = 2
            let s = f.string(from: NSNumber(value: value)) ?? "\(value)"
            return "\(s) \(sign)"
        }
        return "\(int(value)) \(sign)"
    }

    /// "2026-09-12" -> "12.09.26"
    static func etaShort(_ iso: String?) -> String? {
        guard let iso else { return nil }
        let parser = DateFormatter()
        parser.dateFormat = "yyyy-MM-dd"
        parser.locale = Locale(identifier: "en_US_POSIX")
        guard let date = parser.date(from: iso) else { return nil }
        let out = DateFormatter()
        out.dateFormat = "dd.MM.yy"
        return out.string(from: date)
    }

    /// "vor 8 Min" aus dem ISO-updated_at.
    static func freshness(_ iso: String?) -> String? {
        guard let iso else { return nil }
        let parser = ISO8601DateFormatter()
        guard let date = parser.date(from: iso) else { return nil }
        let rel = RelativeDateTimeFormatter()
        rel.unitsStyle = .short
        return rel.localizedString(for: date, relativeTo: Date())
    }
}
