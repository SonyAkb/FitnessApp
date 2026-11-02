package com.fitquest.app.workout;

import static org.junit.Assert.*;

import com.fitquest.app.workout.SessionProgress.ExerciseEntry;
import com.fitquest.app.workout.SessionProgress.SetEntry;
import com.fitquest.app.workout.SessionProgress.SetStatus;

import java.util.Arrays;

import org.junit.Test;

public class SessionProgressTest {

    private SessionProgress build() {
        ExerciseEntry squats = new ExerciseEntry("Squats");
        squats.sets.add(new SetEntry(10, 20.0));
        squats.sets.add(new SetEntry(10, 20.0));
        ExerciseEntry pushups = new ExerciseEntry("Push-ups");
        pushups.sets.add(new SetEntry(15, null));
        return new SessionProgress(Arrays.asList(squats, pushups));
    }

    @Test
    public void navigation_movesWithinBounds() {
        SessionProgress p = build();
        assertFalse(p.previous());
        assertTrue(p.next());
        assertEquals(1, p.currentIndex());
        assertFalse(p.next());
    }

    @Test
    public void markDone_storesActualValues() {
        SessionProgress p = build();
        p.markDone(0, 12, 22.5);
        SetEntry set = p.currentExercise().sets.get(0);
        assertEquals(SetStatus.DONE, set.status);
        assertEquals(Integer.valueOf(12), set.actualReps);
        assertEquals(Double.valueOf(22.5), set.actualWeightKg);
    }

    @Test
    public void skipExercise_skipsPendingAndMovesNext() {
        SessionProgress p = build();
        p.markDone(0, 10, 20.0);
        p.skipExercise();
        assertEquals(1, p.currentIndex());
        assertEquals(1, p.pendingSets()); // остался только подход отжиманий
    }

    @Test
    public void progress_countsDoneAndSkipped() {
        SessionProgress p = build();
        assertEquals(0, p.progressPercent());
        p.markDone(0, 10, 20.0);
        p.skipSet(1);
        assertEquals(66, p.progressPercent());
        assertFalse(p.isAllResolved());
        p.next();
        p.markDone(0, 15, null);
        assertTrue(p.isAllResolved());
        assertEquals(100, p.progressPercent());
    }

    @Test(expected = IllegalArgumentException.class)
    public void markDone_rejectsZeroReps() {
        build().markDone(0, 0, null);
    }
}