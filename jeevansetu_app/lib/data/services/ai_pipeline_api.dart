import 'dart:convert';

import 'package:http/http.dart' as http;

import '../../core/constants/app_constants.dart';

class AIPipelineApi {
  AIPipelineApi({
    http.Client? client,
    String? baseUrl,
    String? authToken,
  })  : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConstants.backendBaseUrl,
        _authToken = authToken ?? AppConstants.backendAuthToken;

  final http.Client _client;
  final String _baseUrl;
  final String _authToken;

  bool get hasAuthToken => _authToken.trim().isNotEmpty;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (hasAuthToken) 'Authorization': 'Bearer $_authToken',
      };

  Future<Map<String, dynamic>> processSensorPacket({
    required Map<String, dynamic> sensorData,
    double responseDelay = 15,
    bool autoEscalate = false,
  }) async {
    final uri = Uri.parse('$_baseUrl/ai/pipeline/process');
    final response = await _client.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'sensor_data': sensorData,
        'response_delay': responseDelay,
        'auto_escalate': autoEscalate,
      }),
    );

    return _decodeResponse(response);
  }

  Future<Map<String, dynamic>> verifyIncident({
    required String incidentId,
    required bool safe,
    double? responseDelay,
  }) async {
    final uri = Uri.parse('$_baseUrl/ai/pipeline/$incidentId/verify');
    final response = await _client.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'safe': safe,
        if (responseDelay != null) 'response_delay': responseDelay,
      }),
    );

    return _decodeResponse(response);
  }

  Future<Map<String, dynamic>> escalateIncident(String incidentId) async {
    final uri = Uri.parse('$_baseUrl/ai/pipeline/$incidentId/escalate');
    final response = await _client.post(uri, headers: _headers);
    return _decodeResponse(response);
  }

  Map<String, dynamic> _decodeResponse(http.Response response) {
    final body = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body) as Map<String, dynamic>;

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body['detail'] ?? 'AI pipeline request failed';
      throw AIPipelineException(response.statusCode, detail.toString());
    }

    return body;
  }
}

class AIPipelineException implements Exception {
  AIPipelineException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'AIPipelineException($statusCode): $message';
}
