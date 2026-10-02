package com.fitquest.app.ui.telemetry;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.fitquest.app.FitQuestApp;
import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.ApiConfig;
import com.fitquest.app.api.dto.DeviceRegisterRequest;
import com.fitquest.app.api.dto.TelemetryDto;
import com.fitquest.app.databinding.FragmentTelemetryBinding;
import com.fitquest.app.databinding.ItemSessionBinding;
import com.fitquest.app.ui.UiFormat;
import com.fitquest.app.ws.TelemetryWebSocket;

import java.util.ArrayList;
import java.util.List;

public class TelemetryFragment extends Fragment {

    private FragmentTelemetryBinding binding;
    private final TelemetryWebSocket socket = new TelemetryWebSocket();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final List<TelemetryDto> history = new ArrayList<>();
    private HistoryAdapter adapter;
    private boolean polling;
    private final Runnable pollRunnable = new Runnable() {
        @Override
        public void run() {
            if (!polling || binding == null) {
                return;
            }
            refreshLatest();
            handler.postDelayed(this, 5000);
        }
    };

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentTelemetryBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        adapter = new HistoryAdapter();
        binding.history.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.history.setAdapter(adapter);
        binding.btnSimulate.setOnClickListener(v -> simulate());
        binding.btnRegister.setOnClickListener(v -> registerDevice());
        binding.btnPoll.setOnClickListener(v -> startPolling("Manual REST poll"));
        binding.swipe.setOnRefreshListener(this::refreshAll);
    }

    @Override
    public void onResume() {
        super.onResume();
        connectLive();
        refreshAll();
    }

    @Override
    public void onPause() {
        polling = false;
        handler.removeCallbacks(pollRunnable);
        socket.close();
        super.onPause();
    }

    private void connectLive() {
        String token = FitQuestApp.get().session().getAccessToken();
        String base = ApiConfig.getBaseUrl(requireContext());
        socket.connect(base, token, new TelemetryWebSocket.Listener() {
            @Override
            public void onSample(TelemetryDto sample) {
                if (getActivity() == null) {
                    return;
                }
                requireActivity().runOnUiThread(() -> bindLatest(sample, "Live socket"));
            }

            @Override
            public void onStatus(String status) {
                if (getActivity() == null) {
                    return;
                }
                requireActivity().runOnUiThread(() -> {
                    if (binding != null) {
                        binding.status.setText(status);
                    }
                });
            }

            @Override
            public void onFailed(String reason) {
                if (getActivity() == null) {
                    return;
                }
                requireActivity().runOnUiThread(() -> startPolling("WS failed: " + reason + " — polling REST"));
            }
        });
    }

    private void startPolling(String reason) {
        if (binding != null) {
            binding.status.setText(reason);
        }
        if (polling) {
            return;
        }
        polling = true;
        handler.removeCallbacks(pollRunnable);
        handler.post(pollRunnable);
    }

    private void refreshAll() {
        refreshLatest();
        ApiCalls.enqueue(ApiClient.get().getTelemetryHistory(), list -> {
            history.clear();
            if (list != null) {
                history.addAll(list);
            }
            adapter.notifyDataSetChanged();
            if (binding != null) {
                binding.swipe.setRefreshing(false);
                binding.emptyHistory.setVisibility(history.isEmpty() ? View.VISIBLE : View.GONE);
            }
        }, err -> {
            if (binding != null) {
                binding.swipe.setRefreshing(false);
            }
        });
    }

    private void refreshLatest() {
        ApiCalls.enqueue(ApiClient.get().getLatestTelemetry(), dto -> bindLatest(dto, binding.status.getText().toString()), err -> {
            if (binding != null && !socket.isOpened()) {
                binding.hint.setText(err);
            }
        });
    }

    private void bindLatest(TelemetryDto dto, String status) {
        if (binding == null || dto == null) {
            return;
        }
        binding.status.setText(status);
        binding.heart.setText(UiFormat.dash(dto.heart_rate));
        binding.steps.setText(UiFormat.dash(dto.steps));
        binding.calories.setText(UiFormat.dash(dto.calories));
        binding.source.setText((dto.source == null ? "unknown" : dto.source)
                + (dto.timestamp == null ? "" : " · " + dto.timestamp));
        binding.hint.setText("");
    }

    private void simulate() {
        ApiCalls.enqueue(ApiClient.get().simulateTelemetry(), dto -> {
            toast("Simulated a beat");
            bindLatest(dto, "Simulated sample");
            refreshAll();
        }, this::toast);
    }

    private void registerDevice() {
        ApiCalls.enqueue(ApiClient.get().registerDevice(new DeviceRegisterRequest("FitQuest emulator")), device -> {
            if (device != null && device.device_id != null) {
                FitQuestApp.get().session().setDeviceId(device.device_id);
                toast("Device " + device.device_id + " registered");
            } else {
                toast("Device registered");
            }
        }, this::toast);
    }

    private void toast(String msg) {
        Toast.makeText(requireContext(), msg, Toast.LENGTH_LONG).show();
    }

    @Override
    public void onDestroyView() {
        polling = false;
        handler.removeCallbacks(pollRunnable);
        socket.close();
        binding = null;
        super.onDestroyView();
    }

    private class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.VH> {
        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemSessionBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            TelemetryDto t = history.get(position);
            holder.binding.title.setText("♥ " + UiFormat.dash(t.heart_rate) + "  ·  " + UiFormat.dash(t.steps) + " steps");
            holder.binding.meta.setText(UiFormat.dash(t.calories) + " kcal"
                    + (t.timestamp == null ? "" : " · " + t.timestamp));
        }

        @Override
        public int getItemCount() {
            return history.size();
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemSessionBinding binding;

            VH(ItemSessionBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }
}
