import { Provider } from 'react-redux';
import { store } from './app/store';
import { api } from './services/api';
import { Dashboard } from './features/dashboard/Dashboard';
import ErrorBoundary from './components/common/ErrorBoundary';

store.dispatch(api.util.resetApiState());

const App = () => {
  return (
    <Provider store={store}>
      <ErrorBoundary>
        <Dashboard />
      </ErrorBoundary>
    </Provider>
  );
};

export default App;