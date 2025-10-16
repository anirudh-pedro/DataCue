import { initializeApp } from 'firebase/app';
import { getAnalytics, isSupported } from 'firebase/analytics';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: 'AIzaSyAk-Y-Vj9XfS1j8a5cyGs1Lru2CFMqrEJw',
  authDomain: 'datacue-50971.firebaseapp.com',
  projectId: 'datacue-50971',
  storageBucket: 'datacue-50971.firebasestorage.app',
  messagingSenderId: '803362972375',
  appId: '1:803362972375:web:8629cd724acbeb6c134692',
  measurementId: 'G-1012CWYZQH',
};

const firebaseApp = initializeApp(firebaseConfig);

const analyticsPromise = typeof window !== 'undefined'
  ? isSupported()
      .then((supported) => (supported ? getAnalytics(firebaseApp) : null))
      .catch(() => null)
  : Promise.resolve(null);

const auth = getAuth(firebaseApp);
const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

export { firebaseApp, analyticsPromise, auth, googleProvider };
