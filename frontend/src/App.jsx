import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import ErrorDetail from './pages/errors/ErrorDetail.jsx'
import ErrorEdit from './pages/errors/ErrorEdit.jsx'
import ErrorList from './pages/errors/ErrorList.jsx'
import ErrorNew from './pages/errors/ErrorNew.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import PublicList from './pages/public/PublicList.jsx'
import Settings from './pages/Settings.jsx'
import SignUp from './pages/SignUp.jsx'
import StudyDetail from './pages/studies/StudyDetail.jsx'
import StudyEdit from './pages/studies/StudyEdit.jsx'
import StudyList from './pages/studies/StudyList.jsx'
import StudyNew from './pages/studies/StudyNew.jsx'
import TodoEdit from './pages/todos/TodoEdit.jsx'
import TodoList from './pages/todos/TodoList.jsx'
import TodoNew from './pages/todos/TodoNew.jsx'

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
          <Route path="/todos" element={<TodoList />} />
          <Route path="/todos/new" element={<TodoNew />} />
          <Route path="/todos/:id/edit" element={<TodoEdit />} />
          <Route path="/public" element={<PublicList />} />
          <Route path="/errors" element={<ErrorList />} />
          <Route path="/errors/new" element={<ErrorNew />} />
          <Route path="/errors/:id" element={<ErrorDetail />} />
          <Route path="/errors/:id/edit" element={<ErrorEdit />} />
        </Route>
      </Route>
    </Routes>
  )
}
