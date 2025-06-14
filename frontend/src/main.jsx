import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import './index.css';
import {store} from './services/storage/store.js'
import App from './App.jsx';
import './singletons/'

const savedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const useDark = savedTheme ? savedTheme === 'dark' : prefersDark;
document.documentElement.classList.toggle('dark', useDark);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </StrictMode>
);
