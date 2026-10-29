package com.fitquest.app.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

import com.fitquest.app.R;
import org.junit.Test;

/** US-D1/D2: the client only maps the server mood to a picture and a line. */
public class UiFormatTest {

    @Test
    public void moodSelectsFoxPicture() {
        assertEquals(R.drawable.fox_happy, UiFormat.foxForMood("happy"));
        assertEquals(R.drawable.fox_sad, UiFormat.foxForMood("SAD"));
        assertEquals(R.drawable.fox_level_up, UiFormat.foxForMood("level_up"));
    }

    /** PET-06 (D-14): neutral и sleeping получают собственные картинки. */
    @Test
    public void moodThresholdPicturesForNeutralAndSleeping() {
        assertEquals(R.drawable.fox_neutral, UiFormat.foxForMood("neutral"));
        assertEquals(R.drawable.fox_sleeping, UiFormat.foxForMood("SLEEPING"));
        assertNotEquals(UiFormat.foxForMood("sleeping"), UiFormat.foxForMood("sad"));
        assertNotEquals(UiFormat.moodLine("sleeping"), UiFormat.moodLine("neutral"));
    }

    @Test
    public void unknownOrMissingMoodFallsBackToIdle() {
        assertEquals(R.drawable.fox_idle, UiFormat.foxForMood(null));
        assertEquals(R.drawable.fox_idle, UiFormat.foxForMood("bogus-mood"));
    }

    @Test
    public void moodLinesDifferForHappyAndSad() {
        assertNotEquals(UiFormat.moodLine("happy"), UiFormat.moodLine("sad"));
        assertEquals("Waiting for you", UiFormat.moodLine(null));
    }
}
