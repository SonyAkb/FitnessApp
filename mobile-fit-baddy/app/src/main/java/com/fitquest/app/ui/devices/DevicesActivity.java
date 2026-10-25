package com.fitquest.app.ui.devices;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.ApiConfig;
import com.fitquest.app.api.dto.DeviceInfoDto;
import com.fitquest.app.api.dto.TelemetryBatchRequest;
import com.fitquest.app.databinding.ActivityDevicesBinding;
import com.fitquest.app.databinding.ItemDeviceBinding;
import com.fitquest.app.health.HealthConnectSource;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Data sources: connect a Raspberry Pi by a pairing code or a watch through Health Connect.
 * The phone never talks to the Pi: both only talk to the backend, the app reads telemetry from it.
 */
public class DevicesActivity extends AppCompatActivity {

    private static final long PAIRING_POLL_MS = 3000;
    private static final long PAIRING_TIMEOUT_MS = 10 * 60 * 1000L;

    private ActivityDevicesBinding binding;
    private final List<DeviceInfoDto> devices = new ArrayList<>();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private DeviceAdapter adapter;
    private Set<String> knownBeforePairing;
    private long pairingStartedAt;
    private HealthConnectSource healthConnect;
    private ActivityResultLauncher<String[]> permissionLauncher;

    private final Runnable pairingPoll = new Runnable() {
        @Override
        public void run() {
            if (knownBeforePairing == null || binding == null) {
                return;
            }
            if (System.currentTimeMillis() - pairingStartedAt > PAIRING_TIMEOUT_MS) {
                stopPairing("Code expired. Get a new one.");
                return;
            }
            refreshDevices();
            handler.postDelayed(this, PAIRING_POLL_MS);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityDevicesBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        adapter = new DeviceAdapter();
        binding.devices.setLayoutManager(new LinearLayoutManager(this));
        binding.devices.setAdapter(adapter);
        binding.btnBack.setOnClickListener(v -> finish());
        binding.btnPairPi.setOnClickListener(v -> startPairing());
        binding.btnHealthConnect.setOnClickListener(v -> connectHealthConnect());
        binding.btnSyncHealth.setOnClickListener(v -> syncHealthConnect());
        binding.swipe.setOnRefreshListener(this::refreshDevices);

        permissionLauncher = registerForActivityResult(new ActivityResultContracts.RequestMultiplePermissions(), this::onPermissions);
        if (HealthConnectSource.isSupported()) {
            healthConnect = new HealthConnectSource(this);
        }
        bindHealthConnectState();
        refreshDevices();
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        binding = null;
        super.onDestroy();
    }

    // --- devices list ---------------------------------------------------------

    private void refreshDevices() {
        ApiCalls.enqueue(ApiClient.get().getDevices(), list -> {
            if (binding == null) {
                return;
            }
            devices.clear();
            if (list != null) {
                devices.addAll(list);
            }
            adapter.notifyDataSetChanged();
            binding.swipe.setRefreshing(false);
            binding.emptyDevices.setVisibility(devices.isEmpty() ? View.VISIBLE : View.GONE);
            checkPairingDone();
        }, err -> {
            if (binding != null) {
                binding.swipe.setRefreshing(false);
                binding.status.setText(err);
            }
        });
    }

    private void unlink(DeviceInfoDto device) {
        ApiCalls.enqueue(ApiClient.get().deleteDevice(device.device_id), ignored -> {
            toast(SourceLabels.label(device.kind) + " unlinked");
            refreshDevices();
        }, this::toast);
    }

    // --- Raspberry Pi: pairing code -------------------------------------------

    private void startPairing() {
        Set<String> before = new HashSet<>();
        for (DeviceInfoDto d : devices) {
            before.add(d.device_id);
        }
        ApiCalls.enqueue(ApiClient.get().createPairingCode(), code -> {
            if (binding == null || code == null) {
                return;
            }
            knownBeforePairing = before;
            pairingStartedAt = System.currentTimeMillis();
            binding.pairingCode.setText(code.code);
            binding.pairingCode.setVisibility(View.VISIBLE);
            binding.pairingHint.setText("Start the Pi node with this code (valid 10 min):\n"
                    + "BACKEND_URL=" + SourceLabels.backendUrlForPi(ApiConfig.getBaseUrl(this)) + "\n"
                    + "PUBLISH_ENABLED=true\n"
                    + "PAIRING_CODE=" + code.code + "\n\nWaiting for the Pi…");
            binding.pairingHint.setVisibility(View.VISIBLE);
            handler.removeCallbacks(pairingPoll);
            handler.postDelayed(pairingPoll, PAIRING_POLL_MS);
        }, this::toast);
    }

    private void checkPairingDone() {
        if (knownBeforePairing == null) {
            return;
        }
        for (DeviceInfoDto d : devices) {
            if ("raspberry_pi".equals(d.kind) && !knownBeforePairing.contains(d.device_id)) {
                stopPairing("Connected: " + d.device_id + ". Data appears in Live watch.");
                return;
            }
        }
    }

    private void stopPairing(String message) {
        knownBeforePairing = null;
        handler.removeCallbacks(pairingPoll);
        if (binding != null) {
            binding.pairingCode.setVisibility(View.GONE);
            binding.pairingHint.setText(message);
        }
    }

    // --- Watches: Health Connect ------------------------------------------------

    private void bindHealthConnectState() {
        if (healthConnect == null) {
            binding.healthStatus.setText("Needs Android 14+ with Health Connect. Apple Watch works only with an iPhone.");
            binding.btnHealthConnect.setEnabled(false);
            binding.btnSyncHealth.setEnabled(false);
            return;
        }
        if (!healthConnect.isAvailable()) {
            binding.healthStatus.setText("Health Connect is not available on this device.");
            binding.btnHealthConnect.setEnabled(false);
            binding.btnSyncHealth.setEnabled(false);
            return;
        }
        boolean granted = healthConnect.hasPermissions();
        binding.healthStatus.setText(granted
                ? "Access granted. In Mi Fitness / Zepp / Samsung Health turn on sync to Health Connect."
                : "Allow FitQuest to read steps and heart rate.");
        binding.btnHealthConnect.setEnabled(!granted);
        binding.btnSyncHealth.setEnabled(granted);
    }

    private void connectHealthConnect() {
        if (healthConnect != null) {
            permissionLauncher.launch(HealthConnectSource.PERMISSIONS);
        }
    }

    private void onPermissions(Map<String, Boolean> result) {
        bindHealthConnectState();
        if (healthConnect != null && healthConnect.hasPermissions()) {
            syncHealthConnect();
        } else {
            toast("Without access FitQuest cannot read the watch data.");
        }
    }

    private void syncHealthConnect() {
        if (healthConnect == null || !healthConnect.hasPermissions()) {
            return;
        }
        binding.healthStatus.setText("Reading the last 24 hours…");
        healthConnect.readPoints(points -> {
            if (points.isEmpty()) {
                if (binding != null) {
                    binding.healthStatus.setText("No heart rate in Health Connect for the last 24 hours.");
                }
                return;
            }
            uploadInChunks(points, 0, 0);
        }, err -> {
            if (binding != null) {
                binding.healthStatus.setText(err);
            }
        });
    }

    private void uploadInChunks(List<TelemetryBatchRequest.Point> points, int from, int accepted) {
        int to = Math.min(from + 500, points.size());
        TelemetryBatchRequest body = new TelemetryBatchRequest(new ArrayList<>(points.subList(from, to)));
        ApiCalls.enqueue(ApiClient.get().uploadTelemetryBatch(body), result -> {
            int total = accepted + (result == null ? 0 : result.accepted);
            if (to < points.size()) {
                uploadInChunks(points, to, total);
                return;
            }
            if (binding != null) {
                binding.healthStatus.setText("Synced: " + total + " new points.");
            }
            refreshDevices();
        }, err -> {
            if (binding != null) {
                binding.healthStatus.setText(err);
            }
        });
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private class DeviceAdapter extends RecyclerView.Adapter<DeviceAdapter.VH> {
        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemDeviceBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            DeviceInfoDto d = devices.get(position);
            holder.binding.title.setText(SourceLabels.label(d.kind));
            holder.binding.meta.setText(d.device_id + " · last data: " + SourceLabels.shortTime(d.last_seen_at));
            holder.binding.btnUnlink.setVisibility("simulator".equals(d.kind) ? View.GONE : View.VISIBLE);
            holder.binding.btnUnlink.setOnClickListener(v -> unlink(d));
        }

        @Override
        public int getItemCount() {
            return devices.size();
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemDeviceBinding binding;

            VH(ItemDeviceBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }
}
