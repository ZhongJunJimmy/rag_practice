import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Chat from './pages/Chat';
import UserManagement from './pages/UserManagement';
import DocumentManagement from './pages/DocumentManagement';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Chat />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="documents" element={<DocumentManagement />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;