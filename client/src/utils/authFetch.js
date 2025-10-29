import { auth } from '../firebase';

/**
 * Perform a fetch request with the current Firebase ID token attached.
 */
export const authFetch = async (input, init = {}) => {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('No authenticated user available for authorised request');
  }

  const token = await user.getIdToken();
  const headers = new Headers(init.headers ?? {});
  headers.set('Authorization', `Bearer ${token}`);

  return fetch(input, { ...init, headers });
};
