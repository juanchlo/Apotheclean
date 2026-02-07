/**
 * Componente principal de la aplicación Apotheclean.
 * Configura el router y las rutas de la aplicación.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';
import { Reports } from './pages/admin/Reports';
import { Products } from './pages/admin/Products';
import { Sales } from './pages/admin/Sales';
import { Store } from './pages/user/Store';
import { ProtectedRoute } from './routes/ProtectedRoute';
import './index.css';

/**
 * Componente raíz de la aplicación.
 * Define todas las rutas y su protección.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rutas públicas de autenticación */}
        <Route path="/login" element={<Login />} />
        <Route path="/registro" element={<Register />} />

        {/* Rutas de administrador (protegidas) */}
        <Route
          path="/admin/reportes"
          element={
            <ProtectedRoute requireAdmin>
              <Reports />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/productos"
          element={
            <ProtectedRoute requireAdmin>
              <Products />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/ventas"
          element={
            <ProtectedRoute requireAdmin>
              <Sales />
            </ProtectedRoute>
          }
        />

        {/* Página de productos para usuarios */}
        <Route
          path="/productos"
          element={
            <ProtectedRoute>
              <Store />
            </ProtectedRoute>
          }
        />

        {/* Redirección por defecto */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

