// src/App.tsx
import React from 'react';
import { Provider } from 'react-redux';
import { store } from './app/store';
import { Dashboard } from './features/dashboard/Dashboard';

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <Dashboard />
    </Provider>
  );
};

export default App;

// src/index.tsx
import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);

// src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;