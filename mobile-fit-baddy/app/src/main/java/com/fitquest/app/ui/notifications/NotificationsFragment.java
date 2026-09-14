package com.fitquest.app.ui.notifications;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.fitquest.app.api.ApiCalls;
import com.fitquest.app.api.ApiClient;
import com.fitquest.app.api.dto.NotificationDto;
import com.fitquest.app.databinding.FragmentNotificationsBinding;
import com.fitquest.app.databinding.ItemNotificationBinding;

import java.util.ArrayList;
import java.util.List;

public class NotificationsFragment extends Fragment {

    private FragmentNotificationsBinding binding;
    private final List<NotificationDto> items = new ArrayList<>();
    private Adapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        binding = FragmentNotificationsBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        adapter = new Adapter();
        binding.list.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.list.setAdapter(adapter);
        binding.swipe.setOnRefreshListener(this::load);
    }

    @Override
    public void onResume() {
        super.onResume();
        load();
    }

    private void load() {
        ApiCalls.enqueue(ApiClient.get().getNotifications(), list -> {
            items.clear();
            if (list != null) {
                items.addAll(list);
            }
            adapter.notifyDataSetChanged();
            binding.empty.setVisibility(items.isEmpty() ? View.VISIBLE : View.GONE);
            binding.swipe.setRefreshing(false);
            binding.error.setVisibility(View.GONE);
        }, err -> {
            binding.error.setVisibility(View.VISIBLE);
            binding.error.setText(err);
            binding.swipe.setRefreshing(false);
        });
    }

    @Override
    public void onDestroyView() {
        binding = null;
        super.onDestroyView();
    }

    private class Adapter extends RecyclerView.Adapter<Adapter.VH> {
        @NonNull
        @Override
        public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            return new VH(ItemNotificationBinding.inflate(getLayoutInflater(), parent, false));
        }

        @Override
        public void onBindViewHolder(@NonNull VH holder, int position) {
            NotificationDto n = items.get(position);
            holder.binding.title.setText(n.title == null ? "Note" : n.title);
            holder.binding.body.setText(n.text());
            holder.binding.meta.setText((n.isRead() ? "Read" : "New") + (n.created_at == null ? "" : " · " + n.created_at));
            holder.binding.getRoot().setAlpha(n.isRead() ? 0.6f : 1f);
            holder.binding.getRoot().setOnClickListener(v -> {
                if (n.id == null || n.isRead()) {
                    return;
                }
                ApiCalls.enqueue(ApiClient.get().markNotificationRead(n.id), ignored -> {
                    n.read = true;
                    n.is_read = true;
                    notifyItemChanged(holder.getBindingAdapterPosition());
                }, err -> Toast.makeText(requireContext(), err, Toast.LENGTH_SHORT).show());
            });
        }

        @Override
        public int getItemCount() {
            return items.size();
        }

        class VH extends RecyclerView.ViewHolder {
            final ItemNotificationBinding binding;

            VH(ItemNotificationBinding binding) {
                super(binding.getRoot());
                this.binding = binding;
            }
        }
    }
}
