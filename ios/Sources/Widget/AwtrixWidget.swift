import WidgetKit
import SwiftUI

// MARK: - Timeline

struct AwtrixEntry: TimelineEntry {
    let date: Date
    let snapshot: Snapshot?
}

struct AwtrixProvider: TimelineProvider {
    func placeholder(in context: Context) -> AwtrixEntry {
        AwtrixEntry(date: Date(), snapshot: .preview)
    }

    func getSnapshot(in context: Context, completion: @escaping (AwtrixEntry) -> Void) {
        // Schnelle Vorschau (Widget-Galerie): echte Daten, sonst Beispiel.
        Task {
            let snap = try? await AwtrixAPI.fetch()
            completion(AwtrixEntry(date: Date(), snapshot: snap ?? .preview))
        }
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<AwtrixEntry>) -> Void) {
        Task {
            let snap = try? await AwtrixAPI.fetch()
            let entry = AwtrixEntry(date: Date(), snapshot: snap)
            // Die Uhr-Daten aktualisieren ~alle 15 Min -> Widget alle 30 Min neu
            // anfragen (iOS budgetiert Refreshes; haeufiger lohnt nicht).
            let next = Calendar.current.date(byAdding: .minute, value: 30, to: Date()) ?? Date().addingTimeInterval(1800)
            completion(Timeline(entries: [entry], policy: .after(next)))
        }
    }
}

// MARK: - Widget

struct AwtrixWidget: Widget {
    let kind = "AwtrixWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: AwtrixProvider()) { entry in
            AwtrixWidgetView(entry: entry)
                .containerBackground(Theme.cardBG, for: .widget)
        }
        .configurationDisplayName("AWTRIX Mirror")
        .description("Follower, 100k-Ziel, Einnahmen & Krypto -- wie auf der Uhr.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: - Views

struct AwtrixWidgetView: View {
    @Environment(\.widgetFamily) private var family
    let entry: AwtrixEntry

    var body: some View {
        if let snapshot = entry.snapshot {
            switch family {
            case .systemSmall: SmallView(snapshot: snapshot)
            default:           MediumView(snapshot: snapshot)
            }
        } else {
            UnavailableView()
        }
    }
}

/// Klein: Fokus auf Follower + Tageszuwachs, darunter das 100k-Ziel.
private struct SmallView: View {
    let snapshot: Snapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Label("Follower", systemImage: "person.2.fill")
                .font(.caption2.weight(.semibold))
                .foregroundStyle(Theme.subtle)
            Text(Format.int(snapshot.followers))
                .font(.system(size: 30, weight: .bold, design: .rounded))
                .foregroundStyle(Theme.igPink)
                .minimumScaleFactor(0.6)
                .lineLimit(1)
            if let delta = Format.signedInt(snapshot.followerDelta) {
                Text("\(delta) heute")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Theme.delta(snapshot.followerDelta))
            }
            Spacer(minLength: 0)
            if let missing = snapshot.goalMissing {
                HStack(spacing: 4) {
                    Text("100k")
                        .foregroundStyle(Theme.homeLime)
                    Text("-\(Format.int(missing))")
                        .foregroundStyle(.white)
                    if let eta = Format.etaShort(snapshot.goalEta) {
                        Text("~\(eta)")
                            .foregroundStyle(Theme.subtle)
                    }
                }
                .font(.caption2.weight(.medium))
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
    }
}

/// Mittel: alle drei Themen -- Follower, Ziel, Einnahmen+Krypto.
private struct MediumView: View {
    let snapshot: Snapshot

    var body: some View {
        VStack(spacing: 10) {
            HStack(alignment: .top) {
                stat(
                    title: "Follower",
                    value: Format.int(snapshot.followers),
                    color: Theme.igPink,
                    note: Format.signedInt(snapshot.followerDelta).map { "\($0) heute" },
                    noteColor: Theme.delta(snapshot.followerDelta)
                )
                Spacer()
                stat(
                    title: "Ziel 100k",
                    value: snapshot.goalMissing.map { "-\(Format.int($0))" } ?? "—",
                    color: Theme.homeLime,
                    note: Format.etaShort(snapshot.goalEta).map { "~\($0)" },
                    noteColor: Theme.growthGreen,
                    alignment: .trailing
                )
            }
            Divider().overlay(Color.white.opacity(0.12))
            HStack(alignment: .top) {
                stat(
                    title: "Einnahmen heute",
                    value: Format.money(snapshot.revenueToday, sign: snapshot.currencySign, decimals: true),
                    color: Theme.revenueGreen,
                    note: nil,
                    noteColor: .clear
                )
                Spacer()
                stat(
                    title: "Krypto",
                    value: Format.money(snapshot.cryptoTotal, sign: snapshot.currencySign),
                    color: Theme.homeLime,
                    note: Format.signedPct(snapshot.cryptoPct),
                    noteColor: Theme.delta(snapshot.cryptoPct),
                    alignment: .trailing
                )
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }

    private func stat(title: String, value: String, color: Color,
                      note: String?, noteColor: Color,
                      alignment: HorizontalAlignment = .leading) -> some View {
        VStack(alignment: alignment, spacing: 2) {
            Text(title.uppercased())
                .font(.caption2.weight(.semibold))
                .foregroundStyle(Theme.subtle)
            Text(value)
                .font(.title3.weight(.bold))
                .foregroundStyle(color)
                .minimumScaleFactor(0.6)
                .lineLimit(1)
            if let note {
                Text(note)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(noteColor)
                    .lineLimit(1)
            }
        }
    }
}

private struct UnavailableView: View {
    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: "wifi.exclamationmark")
                .font(.title2)
                .foregroundStyle(Theme.subtle)
            Text("Keine Daten")
                .font(.caption)
                .foregroundStyle(Theme.subtle)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Preview

#Preview(as: .systemMedium) {
    AwtrixWidget()
} timeline: {
    AwtrixEntry(date: .now, snapshot: .preview)
    AwtrixEntry(date: .now, snapshot: nil)
}
