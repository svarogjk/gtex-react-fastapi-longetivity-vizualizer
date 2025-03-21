import React from 'react';
import { Provider } from 'react-redux';
import { store } from './app/store';
import { api } from './services/api';
import { Dashboard } from './features/dashboard/Dashboard';
import ErrorBoundary from './components/common/ErrorBoundary';

store.dispatch(api.util.resetApiState());

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