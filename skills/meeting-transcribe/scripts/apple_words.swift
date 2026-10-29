// Apple の音声認識（macOS 26 SpeechAnalyzer / SpeechTranscriber）で音声ファイルを文字起こしし、
// 認識単位（ほぼ1文字）ごとの時刻を TSV で出す。処理は Mac の中だけで行う（初回のみ言語データを自動ダウンロード）。
// 使い方: apple_words <audio> [locale=ja-JP] > words.tsv   （列: 開始秒 / 終了秒 / テキスト）
import AVFoundation
import Foundation
import Speech

func log(_ s: String) { FileHandle.standardError.write("[apple_words] \(s)\n".data(using: .utf8)!) }

let args = CommandLine.arguments
guard args.count >= 2 else { log("usage: apple_words <audio> [locale]"); exit(2) }
let url = URL(fileURLWithPath: args[1])
let locale = Locale(identifier: args.count >= 3 ? args[2] : "ja-JP")

guard let matched = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else { log("locale not supported: \(locale.identifier)"); exit(1) }
let transcriber = SpeechTranscriber(locale: matched, transcriptionOptions: [], reportingOptions: [], attributeOptions: [.audioTimeRange])
if let req = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
    log("downloading speech assets for \(matched.identifier)")
    try await req.downloadAndInstall()
}

let analyzer = SpeechAnalyzer(modules: [transcriber])
let file = try AVAudioFile(forReading: url)
log("start \(url.lastPathComponent)")

let collector = Task {
    var n = 0
    for try await r in transcriber.results {
        for run in r.text.runs {
            guard let tr = run.audioTimeRange else { continue }
            print(String(format: "%.2f\t%.2f\t%@", tr.start.seconds, tr.end.seconds, String(r.text[run.range].characters)))
            n += 1
        }
    }
    return n
}

if let last = try await analyzer.analyzeSequence(from: file) {
    try await analyzer.finalizeAndFinish(through: last)
} else {
    await analyzer.cancelAndFinishNow()
}
log("done units=\(try await collector.value)")
