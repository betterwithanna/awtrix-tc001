import Foundation

/// Spiegel der Werte, die main.py nach Supabase schreibt (RPC awtrix_get_snapshot).
/// Alle Felder optional: fehlt eine Quelle, bleibt das jeweilige Feld leer.
struct Snapshot: Codable, Equatable {
    var followers: Double?
    var followerDelta: Double?
    var goalTarget: Double?
    var goalMissing: Double?
    var goalEta: String?          // ISO-Datum "YYYY-MM-DD"
    var revenueToday: Double?
    var cryptoTotal: Double?
    var cryptoPct: Double?
    var cryptoEur: Double?
    var currency: String?
    var updatedAt: String?        // ISO-8601 "YYYY-MM-DDTHH:MM:SSZ"

    enum CodingKeys: String, CodingKey {
        case followers
        case followerDelta = "follower_delta"
        case goalTarget = "goal_target"
        case goalMissing = "goal_missing"
        case goalEta = "goal_eta"
        case revenueToday = "revenue_today"
        case cryptoTotal = "crypto_total"
        case cryptoPct = "crypto_pct"
        case cryptoEur = "crypto_eur"
        case currency
        case updatedAt = "updated_at"
    }

    var currencySign: String { (currency?.isEmpty == false) ? currency! : "EUR" }

    /// Beispieldaten fuer Xcode-Preview und Platzhalter im Widget.
    static let preview = Snapshot(
        followers: 84210,
        followerDelta: 123,
        goalTarget: 100_000,
        goalMissing: 15_790,
        goalEta: "2026-09-12",
        revenueToday: 248.50,
        cryptoTotal: 7421.00,
        cryptoPct: 2.4,
        cryptoEur: 174.0,
        currency: "EUR",
        updatedAt: nil
    )
}
