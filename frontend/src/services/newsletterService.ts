import { api } from '../utils/api';

export async function subscribeToNewsletter(email: string, firstName?: string) {
  return api.post('/newsletter/subscribe', {
    email,
    first_name: firstName,
  });
}

export async function unsubscribeFromNewsletter(email: string) {
  return api.post('/newsletter/unsubscribe', {
    email,
  });
}

export default {
  subscribeToNewsletter,
  unsubscribeFromNewsletter,
};

