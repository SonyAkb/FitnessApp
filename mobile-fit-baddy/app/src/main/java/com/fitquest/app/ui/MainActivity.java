package com.fitquest.app.ui;

import android.content.Intent;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.R;
import com.fitquest.app.databinding.ActivityMainBinding;
import com.fitquest.app.ui.home.HomeFragment;
import com.fitquest.app.ui.notifications.NotificationsFragment;
import com.fitquest.app.ui.profile.ProfileFragment;
import com.fitquest.app.ui.progress.ProgressFragment;
import com.fitquest.app.ui.workout.WorkoutFragment;

public class MainActivity extends AppCompatActivity implements FitQuestApp.UnauthorizedListener {

    private ActivityMainBinding binding;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        FitQuestApp.get().addUnauthorizedListener(this);

        binding.bottomNav.setOnItemSelectedListener(item -> {
            Fragment fragment = fragmentFor(item.getItemId());
            getSupportFragmentManager()
                    .beginTransaction()
                    .replace(R.id.fragmentContainer, fragment)
                    .commit();
            return true;
        });

        if (savedInstanceState == null) {
            binding.bottomNav.setSelectedItemId(R.id.nav_home);
        }
    }

    @NonNull
    private Fragment fragmentFor(int itemId) {
        if (itemId == R.id.nav_workout) {
            return new WorkoutFragment();
        }
        if (itemId == R.id.nav_progress) {
            return new ProgressFragment();
        }
        if (itemId == R.id.nav_alerts) {
            return new NotificationsFragment();
        }
        if (itemId == R.id.nav_profile) {
            return new ProfileFragment();
        }
        return new HomeFragment();
    }

    public void openWorkoutTab() {
        binding.bottomNav.setSelectedItemId(R.id.nav_workout);
    }

    @Override
    protected void onDestroy() {
        FitQuestApp.get().removeUnauthorizedListener(this);
        super.onDestroy();
    }

    @Override
    public void onUnauthorized() {
        runOnUiThread(() -> {
            Intent intent = new Intent(this, AuthActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            finish();
        });
    }
}
