import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import PositionsPage from './pages/PositionsPage'
import RunsPage from './pages/RunsPage'
import RunDetailPage from './pages/RunDetailPage'
import ResearchPage from './pages/ResearchPage'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<PositionsPage />} />
          <Route path="/runs" element={<RunsPage />} />
          <Route path="/runs/:id" element={<RunDetailPage />} />
          <Route path="/research" element={<ResearchPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
