class AppConstants {
  AppConstants._();

  // App Info
  static const String appName = 'JeevanSetu';
  static const String appTagline = 'Smart Accident Detection';
  static const String appVersion = '1.0.0';
  static const String backendBaseUrl = String.fromEnvironment(
    'JEEVANSETU_API_BASE_URL',
    defaultValue: 'http://localhost:8000/api',
  );
  static const String backendAuthToken = String.fromEnvironment(
    'JEEVANSETU_AUTH_TOKEN',
    defaultValue: '',
  );

  // Timing
  static const int splashDuration = 2500; // ms
  static const int countdownSeconds = 15;
  static const int otpLength = 6;
  static const int otpResendDelay = 30; // seconds

  // UI
  static const double cardRadius = 16.0;
  static const double buttonRadius = 12.0;
  static const double screenPadding = 20.0;
  static const double cardPadding = 16.0;

  // Mock location (New Delhi)
  static const double mockLatitude = 28.6139;
  static const double mockLongitude = 77.2090;
}
