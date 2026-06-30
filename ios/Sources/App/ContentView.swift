import SwiftUI

/// Begleit-App: zeigt dieselben Werte wie das Widget und dient als Vorschau /
/// Smoke-Test der Supabase-Verbindung. Das eigentliche Ziel ist das Widget.
struct ContentView: View {
    @State private var snapshot: Snapshot?
    @State private var error: String?
    @State private var loading = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    if let snapshot {
                        MetricRow(
                            title: "Follower",
                            value: Format.int(snapshot.followers),
                            valueColor: Theme.igPink,
                            trailing: Format.signedInt(snapshot.followerDelta),
                            trailingColor: Theme.delta(snapshot.followerDelta)
                        )
                        MetricRow(
                            title: "Ziel 100k",
                            value: snapshot.goalMissing.map { "-\(Format.int($0))" } ?? "—",
                            valueColor: Theme.homeLime,
                            trailing: Format.etaShort(snapshot.goalEta).map { "~\($0)" },
                            trailingColor: Theme.growthGreen
                        )
                        MetricRow(
                            title: "Einnahmen heute",
                            value: Format.money(snapshot.revenueToday, sign: snapshot.currencySign, decimals: true),
                            valueColor: Theme.revenueGreen,
                            trailing: nil,
                            trailingColor: .clear
                        )
                        MetricRow(
                            title: "Krypto (BTC+SOL)",
                            value: Format.money(snapshot.cryptoTotal, sign: snapshot.currencySign),
                            valueColor: Theme.homeLime,
                            trailing: Format.signedPct(snapshot.cryptoPct),
                            trailingColor: Theme.delta(snapshot.cryptoPct)
                        )

                        if let fresh = Format.freshness(snapshot.updatedAt) {
                            Text("Aktualisiert \(fresh)")
                                .font(.footnote)
                                .foregroundStyle(Theme.subtle)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    } else if let error {
                        ContentUnavailableView("Keine Verbindung", systemImage: "wifi.exclamationmark", description: Text(error))
                    } else {
                        ProgressView().padding(.top, 60)
                    }
                }
                .padding()
            }
            .navigationTitle("AWTRIX Mirror")
            .toolbar {
                Button {
                    Task { await load() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .disabled(loading)
            }
        }
        .task { await load() }
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do {
            snapshot = try await AwtrixAPI.fetch()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }
}

private struct MetricRow: View {
    let title: String
    let value: String
    let valueColor: Color
    let trailing: String?
    let trailingColor: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title.uppercased())
                .font(.caption.weight(.semibold))
                .foregroundStyle(Theme.subtle)
            HStack(alignment: .firstTextBaseline) {
                Text(value)
                    .font(.title2.weight(.bold))
                    .foregroundStyle(valueColor)
                Spacer()
                if let trailing {
                    Text(trailing)
                        .font(.headline)
                        .foregroundStyle(trailingColor)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Theme.cardBG, in: RoundedRectangle(cornerRadius: 14))
    }
}

#Preview {
    ContentView()
}
