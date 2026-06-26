import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../data/services/ai_pipeline_api.dart';
import '../../../data/models/contact_model.dart';
import '../../../data/mock/mock_data.dart';

enum AccidentStatus {
  none,
  detecting, // showing countdown
  resolvedSafe, // user clicked safe
  confirmed, // countdown hit 0 or manual SOS clicked
}

class EmergencyState {
  final AccidentStatus status;
  final int countdownSeconds;
  final int severityScore;
  final String severityLevel; // 'Critical', 'Moderate', 'Minor'
  final List<ContactModel> contacts;
  final bool isAlertingContacts;
  final String? activeIncidentId;
  final String? recommendedHospital;
  final String? hospitalEta;
  final String? errorMessage;

  EmergencyState({
    required this.status,
    required this.countdownSeconds,
    required this.severityScore,
    required this.severityLevel,
    required this.contacts,
    required this.isAlertingContacts,
    this.activeIncidentId,
    this.recommendedHospital,
    this.hospitalEta,
    this.errorMessage,
  });

  EmergencyState copyWith({
    AccidentStatus? status,
    int? countdownSeconds,
    int? severityScore,
    String? severityLevel,
    List<ContactModel>? contacts,
    bool? isAlertingContacts,
    String? activeIncidentId,
    bool clearActiveIncidentId = false,
    String? recommendedHospital,
    String? hospitalEta,
    String? errorMessage,
    bool clearErrorMessage = false,
  }) {
    return EmergencyState(
      status: status ?? this.status,
      countdownSeconds: countdownSeconds ?? this.countdownSeconds,
      severityScore: severityScore ?? this.severityScore,
      severityLevel: severityLevel ?? this.severityLevel,
      contacts: contacts ?? this.contacts,
      isAlertingContacts: isAlertingContacts ?? this.isAlertingContacts,
      activeIncidentId: clearActiveIncidentId ? null : activeIncidentId ?? this.activeIncidentId,
      recommendedHospital: recommendedHospital ?? this.recommendedHospital,
      hospitalEta: hospitalEta ?? this.hospitalEta,
      errorMessage: clearErrorMessage ? null : errorMessage ?? this.errorMessage,
    );
  }
}

class EmergencyNotifier extends StateNotifier<EmergencyState> {
  EmergencyNotifier({AIPipelineApi? aiPipelineApi})
      : _aiPipelineApi = aiPipelineApi ?? AIPipelineApi(),
        super(EmergencyState(
          status: AccidentStatus.none,
          countdownSeconds: 15,
          severityScore: 0,
          severityLevel: 'Safe',
          contacts: MockData.mockContacts,
          isAlertingContacts: false,
        ));

  Timer? _countdownTimer;
  final AIPipelineApi _aiPipelineApi;

  Future<void> startCountdown() async {
    _countdownTimer?.cancel();
    state = state.copyWith(
      status: AccidentStatus.detecting,
      countdownSeconds: 15,
      activeIncidentId: 'LOCAL_${DateTime.now().millisecondsSinceEpoch}',
      clearErrorMessage: true,
    );

    await _processSensorPacket();

    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (state.countdownSeconds > 1) {
        state = state.copyWith(countdownSeconds: state.countdownSeconds - 1);
      } else {
        _countdownTimer?.cancel();
        confirmAccident();
      }
    });
  }

  Future<void> cancelAccident() async {
    _countdownTimer?.cancel();
    final incidentId = state.activeIncidentId;
    if (_aiPipelineApi.hasAuthToken && incidentId != null && !incidentId.startsWith('LOCAL_')) {
      try {
        await _aiPipelineApi.verifyIncident(
          incidentId: incidentId,
          safe: true,
          responseDelay: (15 - state.countdownSeconds).toDouble(),
        );
      } catch (error) {
        state = state.copyWith(errorMessage: error.toString());
      }
    }

    state = state.copyWith(
      status: AccidentStatus.resolvedSafe,
      countdownSeconds: 15,
      clearActiveIncidentId: true,
    );
  }

  Future<void> confirmAccident() async {
    _countdownTimer?.cancel();
    final incidentId = state.activeIncidentId;

    if (_aiPipelineApi.hasAuthToken && incidentId != null && !incidentId.startsWith('LOCAL_')) {
      try {
        final response = await _aiPipelineApi.verifyIncident(
          incidentId: incidentId,
          safe: false,
          responseDelay: 15,
        );
        _applyPipelineResponse(response);
      } catch (error) {
        state = state.copyWith(errorMessage: error.toString());
      }
    }

    state = state.copyWith(
      status: AccidentStatus.confirmed,
      countdownSeconds: 0,
      isAlertingContacts: true,
      severityScore: state.severityScore == 0 ? 92 : state.severityScore,
      severityLevel: state.severityLevel == 'Safe' ? 'Critical' : state.severityLevel,
    );

    // Simulate sending SMS alerts to contacts
    Future.delayed(const Duration(seconds: 2), () {
      state = state.copyWith(isAlertingContacts: false);
    });
  }

  Future<void> _processSensorPacket() async {
    if (!_aiPipelineApi.hasAuthToken) {
      _applyDemoPipelineResult();
      return;
    }

    try {
      final result = await _aiPipelineApi.processSensorPacket(
        sensorData: _demoSensorPacket(),
        responseDelay: 0,
      );
      _applyPipelineProcessResult(result);
    } catch (error) {
      state = state.copyWith(errorMessage: error.toString());
      _applyDemoPipelineResult();
    }
  }

  void _applyPipelineProcessResult(Map<String, dynamic> result) {
    final response = result['response'] as Map<String, dynamic>? ?? result;
    _applyPipelineResponse(response);
  }

  void _applyPipelineResponse(Map<String, dynamic> response) {
    final severity = response['severity']?.toString();
    state = state.copyWith(
      activeIncidentId: response['incident_id']?.toString(),
      severityScore: (response['score'] as num?)?.round() ?? state.severityScore,
      severityLevel: severity == null ? state.severityLevel : _formatSeverity(severity),
      recommendedHospital: response['hospital']?.toString(),
      hospitalEta: response['eta']?.toString(),
      clearErrorMessage: true,
    );
  }

  void _applyDemoPipelineResult() {
    state = state.copyWith(
      severityScore: 92,
      severityLevel: 'Critical',
      recommendedHospital: 'Apollo Trauma Center',
      hospitalEta: '8 min',
    );
  }

  Map<String, dynamic> _demoSensorPacket() {
    return {
      'accelerometer': {'x': 8.0, 'y': 2.0, 'z': 1.0},
      'gyroscope': {'x': 4.0, 'y': 1.5, 'z': 0.5},
      'gps': {
        'latitude': 28.6139,
        'longitude': 77.2090,
        'accuracy_m': 5.0,
      },
      'speed': 12.0,
      'previous_speed': 82.0,
      'timestamp': DateTime.now().toUtc().toIso8601String(),
      'previous_orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0},
      'current_orientation': {'x': 45.0, 'y': 10.0, 'z': 5.0},
      'device_id': 'flutter-demo-device',
    };
  }

  String _formatSeverity(String severity) {
    if (severity.isEmpty) {
      return severity;
    }
    return severity[0].toUpperCase() + severity.substring(1).toLowerCase();
  }

  // ─── Contacts CRUD ───
  void addContact(ContactModel contact) {
    state = state.copyWith(contacts: [...state.contacts, contact]);
  }

  void updateContact(ContactModel updatedContact) {
    state = state.copyWith(
      contacts: state.contacts.map((c) => c.id == updatedContact.id ? updatedContact : c).toList(),
    );
  }

  void deleteContact(String id) {
    state = state.copyWith(
      contacts: state.contacts.where((c) => c.id != id).toList(),
    );
  }
}

final emergencyProvider =
    StateNotifierProvider<EmergencyNotifier, EmergencyState>((ref) {
  return EmergencyNotifier();
});
