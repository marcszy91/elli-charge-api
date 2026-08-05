import AppKit
import Foundation

private struct HelperConfiguration: Decodable {
    let python: String
    let handler: String
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationWillFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.prohibited)
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        guard let callbackURL = urls.first,
              let configurationURL = Bundle.main.url(forResource: "helper-config", withExtension: "json"),
              let configurationData = try? Data(contentsOf: configurationURL),
              let configuration = try? JSONDecoder().decode(HelperConfiguration.self, from: configurationData)
        else {
            application.terminate(nil)
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: configuration.python)
        process.arguments = [configuration.handler, callbackURL.absoluteString]
        process.standardOutput = FileHandle.nullDevice
        process.standardError = FileHandle.nullDevice
        try? process.run()
        application.terminate(nil)
    }
}

let application = NSApplication.shared
let delegate = AppDelegate()
application.delegate = delegate
application.run()
