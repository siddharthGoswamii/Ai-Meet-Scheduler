// import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login     from './pages/Login';
import Dashboard from './pages/Dashboard';
// import Meetings  from './pages/Meetings';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/"          element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        {/* <Route path="/meetings"  element={<Meetings />} /> */}
      </Routes>
    </Router>
  );
}

export default App;