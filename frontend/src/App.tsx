import React from 'react';
import { Provider } from 'react-redux';
import { store } from './app/store';
import { Dashboard } from './features/dashboard/Dashboard';
import ErrorBoundary from './components/common/ErrorBoundary';

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <ErrorBoundary>
        <Dashboard />
      </ErrorBoundary>
    </Provider>
  );
};

export default App;