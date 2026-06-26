import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../core/widgets/gradient_card.dart';
import '../../../../core/router/app_router.dart';
import '../widgets/severity_gauge.dart';
import '../../providers/emergency_provider.dart';

class SeverityResultScreen extends ConsumerWidget {
  const SeverityResultScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(emergencyProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final severityColor = AppColors.severityColor(state.severityScore);
    final incidentId = state.activeIncidentId ?? 'INC_098716';
    final hospital = state.recommendedHospital ?? 'Apollo Trauma Center';
    final eta = state.hospitalEta ?? '8 min';

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Analysis Result'),
        actions: [
          IconButton(
            icon: const Icon(Icons.close_rounded),
            onPressed: () {
              ref.read(emergencyProvider.notifier).cancelAccident();
              context.goNamed(AppRoutes.home);
            },
          ),
        ],
      ),
      body: Container(
        width: double.infinity,
        height: double.infinity,
        color: isDark ? AppColors.surfaceDark : AppColors.surfaceLight,
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // Top status indicator
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: severityColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: severityColor.withOpacity(0.3)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.analytics_rounded, color: severityColor, size: 18),
                      const SizedBox(width: 8),
                      Text(
                        'INCIDENT REPORTED - $incidentId',
                        style: AppTextStyles.labelSmall.copyWith(
                          color: severityColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ).animate().fade().slideY(begin: -0.2, end: 0),

                const SizedBox(height: 24),

                // Radial Severity Gauge
                SeverityGauge(score: state.severityScore)
                    .animate()
                    .scale(duration: 600.ms, curve: Curves.easeOutBack),

                const SizedBox(height: 28),

                // Crash Metrics Card
                GradientCard(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Telemetry Diagnostics',
                        style: AppTextStyles.cardTitle.copyWith(
                          color: isDark ? Colors.white : AppColors.primaryLight,
                        ),
                      ),
                      const SizedBox(height: 16),
                      _buildMetricRow(context, 'Impact Force', '8.4 Gs (Severe)', Icons.speed_rounded, AppColors.criticalRed),
                      const Divider(height: 20),
                      _buildMetricRow(context, 'Deceleration Rate', '72 → 5 km/h', Icons.trending_down_rounded, AppColors.warningAmber),
                      const Divider(height: 20),
                      _buildMetricRow(context, 'Device Orientation', 'Rollover Detected (92°)', Icons.screen_rotation_rounded, AppColors.criticalRed),
                      const Divider(height: 20),
                      _buildMetricRow(context, 'User Response State', 'No Response (15s Timeout)', Icons.timer_rounded, AppColors.warningAmber),
                    ],
                  ),
                ).animate().fade(delay: 200.ms).slideY(begin: 0.1, end: 0),

                const SizedBox(height: 16),

                // Emergency response status card
                GradientCard(
                  padding: const EdgeInsets.all(16),
                  borderColor: AppColors.safeGreen.withOpacity(0.3),
                  gradient: isDark
                      ? const LinearGradient(colors: [Color(0xFF0F2518), Color(0xFF0D1117)])
                      : null,
                  child: Row(
                    children: [
                      const Icon(Icons.mark_email_read_rounded, color: AppColors.safeGreen, size: 24),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Emergency Network Alerted',
                              style: AppTextStyles.labelLarge.copyWith(
                                color: isDark ? Colors.white : AppColors.textPrimaryLight,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Best hospital: $hospital - ETA: $eta',
                              style: AppTextStyles.bodySmall.copyWith(
                                color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ).animate().fade(delay: 300.ms),

                const SizedBox(height: 32),

                // Actions Button Column
                Column(
                  children: [
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () => context.pushNamed(AppRoutes.hospitals),
                        icon: const Icon(Icons.local_hospital_rounded),
                        label: const Text('Recommend Best Hospital'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () => context.pushNamed(AppRoutes.liveTracking),
                        icon: const Icon(Icons.map_rounded, color: AppColors.primary),
                        label: const Text('Open Dispatch Live Tracking'),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextButton(
                      onPressed: () {
                        ref.read(emergencyProvider.notifier).cancelAccident();
                        context.goNamed(AppRoutes.home);
                      },
                      child: Text(
                        'I am Safe (Resolve & Dismiss Alert)',
                        style: AppTextStyles.buttonText.copyWith(
                          color: AppColors.textSecondaryDark,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ],
                ).animate().fade(delay: 400.ms),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMetricRow(BuildContext context, String label, String value, IconData icon, Color iconColor) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Row(
      children: [
        Icon(icon, color: iconColor, size: 20),
        const SizedBox(width: 12),
        Text(
          label,
          style: AppTextStyles.bodyMedium.copyWith(
            color: isDark ? AppColors.textSecondaryDark : AppColors.textSecondaryLight,
          ),
        ),
        const Spacer(),
        Text(
          value,
          style: AppTextStyles.labelLarge.copyWith(
            color: isDark ? Colors.white : AppColors.textPrimaryLight,
          ),
        ),
      ],
    );
  }
}
