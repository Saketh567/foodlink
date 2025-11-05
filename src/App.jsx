import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import ClientDashboard from "./pages/ClientDashboard";
import ClientProfile from "./pages/ClientProfile";
import ClientPhotos from "./pages/ClientPhotos";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="page">             {/* outer flex wrapper */}
        <div className="container">       {/* centered, width-limited */}
          <Routes>
            <Route path="/" element={<Navigate to="/client/dashboard" />} />
            <Route path="/client/dashboard" element={<ClientDashboard />} />
            <Route path="/client/profile"   element={<ClientProfile />} />
            <Route path="/client/photos"    element={<ClientPhotos />} />
          </Routes>
        </div>
      </main>
    </BrowserRouter>
  );
}
  



