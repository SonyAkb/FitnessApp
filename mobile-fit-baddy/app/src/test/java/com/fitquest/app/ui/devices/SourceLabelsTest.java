package com.fitquest.app.ui.devices;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public class SourceLabelsTest {

    @Test
    public void knownSourcesHaveHumanLabels() {
        assertEquals("Raspberry Pi", SourceLabels.label("raspberry_pi"));
        assertEquals("Watch · Health Connect", SourceLabels.label("health_connect"));
        assertEquals("Simulator", SourceLabels.label("simulator"));
        assertEquals("Unknown source", SourceLabels.label(null));
    }

    @Test
    public void emulatorAddressIsNotOfferedToThePi() {
        String hint = SourceLabels.backendUrlForPi("http://10.0.2.2:8000/");
        assertTrue(hint.startsWith("http://localhost:8000"));
        assertTrue(hint.contains("<computer IP in Wi-Fi>"));
        assertEquals("http://192.168.1.10:8000", SourceLabels.backendUrlForPi("http://192.168.1.10:8000/"));
    }

    @Test
    public void serverTimeIsShortened() {
        assertEquals("2026-10-25 14:03 UTC", SourceLabels.shortTime("2026-10-25T14:03:41.123456"));
        assertEquals("never", SourceLabels.shortTime(null));
    }
}
