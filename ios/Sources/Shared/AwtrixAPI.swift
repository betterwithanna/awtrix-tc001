import Foundation

/// Holt den aktuellen Snapshot von Supabase (ein POST auf die RPC, anon-Key).
enum AwtrixAPI {
    static func fetch() async throws -> Snapshot {
        var req = URLRequest(url: Config.snapshotEndpoint)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(Config.supabaseKey, forHTTPHeaderField: "apikey")
        req.setValue("Bearer \(Config.supabaseKey)", forHTTPHeaderField: "Authorization")
        req.httpBody = Data("{}".utf8)
        req.cachePolicy = .reloadIgnoringLocalCacheData
        req.timeoutInterval = 20

        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        // Die RPC liefert das JSON-Objekt direkt (kein Wrapper).
        return try JSONDecoder().decode(Snapshot.self, from: data)
    }
}
