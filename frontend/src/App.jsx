import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import Settings from './pages/Settings.jsx'
import SignUp from './pages/SignUp.jsx'
import StudyDetail from './pages/studies/StudyDetail.jsx'
import StudyEdit from './pages/studies/StudyEdit.jsx'
import StudyList from './pages/studies/StudyList.jsx'
import StudyNew from './pages/studies/StudyNew.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Home />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/studies" element={<StudyList />} />
          <Route path="/studies/new" element={<StudyNew />} />
          <Route path="/studies/:id" element={<StudyDetail />} />
          <Route path="/studies/:id/edit" element={<StudyEdit />} />
        </Route>
      </Route>
    </Routes>
  )
}
