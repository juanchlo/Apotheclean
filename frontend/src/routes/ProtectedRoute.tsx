/**
 * Componente de ruta protegida.
 * Verifica autenticación y opcionalmente rol de admin.
 */

import { Navigate, useLocation } from 'react-router-dom';
import { estaAutenticado, esAdmin } from '../api/auth.api';

interface ProtectedRouteProps {
    /** Componente hijo a renderizar si la autenticación es válida */
    children: React.ReactNode;
    /** Si la ruta requiere rol de administrador */
    requireAdmin?: boolean;
}

/**
 * Envuelve rutas que requieren autenticación.
 * Redirige a /login si no hay sesión válida.
 * Redirige a /productos si se requiere admin y el usuario no lo es.
 */
export function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
    const location = useLocation();

    // Verificar autenticación
    if (!estaAutenticado()) {
        // Guardar la ruta actual para redirigir después del login
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // Verificar rol de admin si es requerido
    if (requireAdmin && !esAdmin()) {
        return <Navigate to="/productos" replace />;
    }

    return <>{children}</>;
}
