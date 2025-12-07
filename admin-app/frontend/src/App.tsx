import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import UserDetails from './pages/UserDetails';
import Activity from './pages/Activity';
import Revenue from './pages/Revenue';
import Subscriptions from './pages/Subscriptions';
import DataHealth from './pages/DataHealth';
import Galleries from './pages/Galleries';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
          <Route path="/users/:userId" element={<UserDetails />} />
          <Route path="/activity" element={<Activity />} />
          <Route path="/revenue" element={<Revenue />} />
          <Route path="/subscriptions" element={<Subscriptions />} />
          <Route path="/data-health" element={<DataHealth />} />
          <Route path="/galleries" element={<Galleries />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;

