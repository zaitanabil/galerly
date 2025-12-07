// Email template service - handles email template operations
import { api } from '../utils/api';

export interface EmailTemplate {
  id: string;
  user_id: string;
  name: string;
  subject: string;
  body: string;
  variables?: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateTemplateData {
  name: string;
  subject: string;
  body: string;
}

export interface UpdateTemplateData {
  name?: string;
  subject?: string;
  body?: string;
}

// List all email templates
export async function listTemplates() {
  return api.get<{ templates: EmailTemplate[] }>('/email-templates');
}

// Get a specific template
export async function getTemplate(templateId: string) {
  return api.get<EmailTemplate>(`/email-templates/${templateId}`);
}

// Create a new template
export async function createTemplate(data: CreateTemplateData) {
  return api.post<EmailTemplate>('/email-templates', data);
}

// Update a template
export async function updateTemplate(templateId: string, data: UpdateTemplateData) {
  return api.put<EmailTemplate>(`/email-templates/${templateId}`, data);
}

// Delete a template
export async function deleteTemplate(templateId: string) {
  return api.delete(`/email-templates/${templateId}`);
}

// Preview a template
export async function previewTemplate(templateId: string, variables?: Record<string, string>) {
  return api.post<{ preview_html: string }>(`/email-templates/${templateId}/preview`, { variables });
}

export default {
  listTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  previewTemplate,
};

