import Foundation

/// Supabase-Zugang fuers Widget.
///
/// URL und publishable Key sind oeffentlich-sicher: RLS ist aktiv und der
/// Zugriff laeuft nur ueber die SECURITY-DEFINER-Funktion `awtrix_get_snapshot`,
/// die ausschliesslich das Anzeige-JSON zurueckgibt (kein Schreibrecht). Es sind
/// dieselben Werte, die bereits im GitHub-Actions-Workflow stehen.
///
/// Bei einem anderen Projekt einfach beide Konstanten ersetzen.
enum Config {
    static let supabaseURL = "https://yayfjzetdpofpcoklwrr.supabase.co"
    static let supabaseKey = "sb_publishable_5LSC86Vn81iJG17-eYLZkQ_mab2MtVp"

    static var snapshotEndpoint: URL {
        URL(string: "\(supabaseURL)/rest/v1/rpc/awtrix_get_snapshot")!
    }
}
