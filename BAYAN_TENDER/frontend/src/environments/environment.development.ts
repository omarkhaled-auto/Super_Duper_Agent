export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  appName: 'Bayan Tender Management System (Development)',
  appVersion: '1.0.0-dev',
  defaultLanguage: 'en',
  supportedLanguages: ['en', 'ar'],
  tokenRefreshThreshold: 300,
  sessionTimeout: 3600000,
  maxFileUploadSize: 10485760,
  allowedFileTypes: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg'],
  pagination: {
    defaultPageSize: 10,
    pageSizeOptions: [10, 25, 50, 100]
  },
  features: {
    enableNotifications: true,
    enableDarkMode: true,
    enableMultiLanguage: true
  }
};
