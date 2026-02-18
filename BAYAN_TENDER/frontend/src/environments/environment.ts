export const environment = {
  production: false,
  apiUrl: 'http://localhost:5555/api',
  appName: 'Bayan Tender Management System',
  appVersion: '1.0.0',
  defaultLanguage: 'en',
  supportedLanguages: ['en', 'ar'],
  tokenRefreshThreshold: 300, // 5 minutes before expiry
  sessionTimeout: 3600000, // 1 hour in milliseconds
  maxFileUploadSize: 10485760, // 10MB in bytes
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
