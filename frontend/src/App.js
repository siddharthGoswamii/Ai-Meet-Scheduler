import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
<<<<<<< HEAD

import Login from './pages/Login';
=======
import Login     from './pages/Login';
>>>>>>> 58265cb8b64437496336f26acc985e2099d249aa
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;