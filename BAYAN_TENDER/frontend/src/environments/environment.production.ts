export const environment = {
  production: true,
  apiUrl: 'https://api.bayan-tender.sa/api/v1',
  appName: 'Bayan Tender Management System',
  appVersion: '1.0.0',
  defaultLanguage: 'en',
  supportedLanguages: ['en', 'ar'],
  tokenRefreshThreshold: 300,
  sessionTimeout: 1800000, // 30 minutes in production
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
