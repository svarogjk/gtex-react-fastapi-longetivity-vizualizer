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