package com.fitquest.app.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

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

    /**
     * AND-14: у happy, sad, sleeping, level_up и neutral — своя покадровая анимация,
     * а не одна общая «idle». Проверяем и ресурс, и что все пять различаются между собой.
     */
    @Test
    public void eachMoodHasItsOwnAnimation() {
        assertEquals(R.drawable.fox_happy_animation, UiFormat.foxAnimationForMood("happy"));
        assertEquals(R.drawable.fox_sad_animation, UiFormat.foxAnimationForMood("SAD"));
        assertEquals(R.drawable.fox_sleeping_animation, UiFormat.foxAnimationForMood("sleeping"));
        assertEquals(R.drawable.fox_level_up_animation, UiFormat.foxAnimationForMood("level_up"));
        assertEquals(R.drawable.fox_neutral_animation, UiFormat.foxAnimationForMood("Neutral"));
        assertDistinct(
                UiFormat.foxAnimationForMood("happy"),
                UiFormat.foxAnimationForMood("sad"),
                UiFormat.foxAnimationForMood("sleeping"),
                UiFormat.foxAnimationForMood("level_up"),
                UiFormat.foxAnimationForMood("neutral"));
    }

    /** AND-14: сон — это именно анимация, а не статичный кадр (PET-06). */
    @Test
    public void sleepingAnimationDiffersFromSleepingStillFrame() {
        assertNotEquals(UiFormat.foxAnimationForMood("sleeping"), UiFormat.foxForMood("sleeping"));
        assertNotEquals(UiFormat.foxAnimationForMood("sleeping"), UiFormat.foxAnimationForMood("sad"));
    }

    /** AND-14: неизвестное/отсутствующее настроение не ломает экран — откат на idle-анимацию. */
    @Test
    public void unknownOrMissingMoodFallsBackToIdleAnimation() {
        assertEquals(R.drawable.fox_idle_animation, UiFormat.foxAnimationForMood(null));
        assertEquals(R.drawable.fox_idle_animation, UiFormat.foxAnimationForMood("bogus-mood"));
        assertEquals(R.drawable.fox_idle_animation, UiFormat.foxAnimationForMood("idle"));
    }

    /** AND-14: вспышка «+XP» после тренировки — отдельный one-shot ресурс. */
    @Test
    public void xpBurstIsItsOwnAnimationResource() {
        assertEquals(R.drawable.xp_gain_animation, UiFormat.xpGainAnimation());
        assertNotEquals(UiFormat.xpGainAnimation(), UiFormat.foxAnimationForMood("happy"));
        assertNotEquals(UiFormat.xpGainAnimation(), UiFormat.foxAnimationForMood("level_up"));
    }

    /** AND-14: level_up проигрывается один раз, зацикленные настроения — нет. */
    @Test
    public void onlyLevelUpIsOneShot() {
        assertTrue(UiFormat.isOneShotAnimation("level_up"));
        assertTrue(UiFormat.isOneShotAnimation("LEVEL_UP"));
        assertFalse(UiFormat.isOneShotAnimation("happy"));
        assertFalse(UiFormat.isOneShotAnimation("sleeping"));
        assertFalse(UiFormat.isOneShotAnimation(null));
    }

    private static void assertDistinct(int... resources) {
        for (int i = 0; i < resources.length; i++) {
            for (int j = i + 1; j < resources.length; j++) {
                assertNotEquals("mood animations must not share a resource", resources[i], resources[j]);
            }
        }
    }
}
