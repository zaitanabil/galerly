// Central export for all API services
// Import this file to access all backend services

export * from './galleryService';
export * from './photoService';
export * from './billingService';
export * from './analyticsService';
export * from './clientService';
export * from './userService';
export * from './publicService';
export * from './emailTemplateService';

// Re-export services as named objects for convenience
import * as galleryService from './galleryService';
import * as photoService from './photoService';
import * as billingService from './billingService';
import * as analyticsService from './analyticsService';
import * as clientService from './clientService';
import * as userService from './userService';
import * as publicService from './publicService';
import * as emailTemplateService from './emailTemplateService';

export {
  galleryService,
  photoService,
  billingService,
  analyticsService,
  clientService,
  userService,
  publicService,
  emailTemplateService,
};

