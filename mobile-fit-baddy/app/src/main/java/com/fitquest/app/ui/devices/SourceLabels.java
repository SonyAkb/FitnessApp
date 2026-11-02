package com.fitquest.app.ui.devices;

/** Human labels for TelemetryDTO.source / device kind (pure, unit-tested). */
public final class SourceLabels {
    private SourceLabels() {
    }

    public static String label(String kind) {
        if (kind == null) {
            return "Unknown source";
        }
        switch (kind) {
            case "raspberry_pi":
                return "Raspberry Pi";
            case "health_connect":
                return "Watch · Health Connect";
            case "simulator":
                return "Simulator";
            default:
                return kind;
        }
    }

    /**
     * The address the Pi should use. The emulator reaches the computer as 10.0.2.2, the node cannot:
     * on the same computer it needs localhost, on a real Pi the computer's LAN address.
     */
    public static String backendUrlForPi(String appBaseUrl) {
        String url = appBaseUrl == null ? "" : appBaseUrl.replaceAll("/+$", "");
        if (url.isEmpty() || url.contains("10.0.2.2") || url.contains("localhost") || url.contains("127.0.0.1")) {
            return "http://localhost:8000   (node on this computer)\n"
                    + "BACKEND_URL=http://<computer IP in Wi-Fi>:8000   (real Pi)";
        }
        return url;
    }

    /** "2026-10-25T14:03:41.123456" → "2026-10-25 14:03" (server time is UTC). */
    public static String shortTime(String iso) {
        if (iso == null || iso.length() < 16) {
            return "never";
        }
        return iso.substring(0, 10) + " " + iso.substring(11, 16) + " UTC";
    }
}
