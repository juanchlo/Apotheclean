import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { obtenerUsuarioActual, logout } from '../../api/auth.api';
import './AdminNavbar.css';

/**
 * Componente de barra de navegación para el panel de administración.
 * Incluye logo, enlaces de navegación y menú de usuario con logout.
 */
export function AdminNavbar() {
    const navigate = useNavigate();
    const location = useLocation();
    const usuario = obtenerUsuarioActual();
    const [menuAbierto, setMenuAbierto] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isActive = (path: string) => {
        return location.pathname.startsWith(path) ? 'active' : '';
    };

    return (
        <header className="admin-header">
            <div className="admin-header-content">
                {/* Logo */}
                <div className="admin-logo">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z" />
                        <path d="M2 17l10 5 10-5" />
                        <path d="M2 12l10 5 10-5" />
                    </svg>
                    <span>Apotheclean</span>
                </div>

                {/* Navegación */}
                <nav className="admin-nav">
                    <Link to="/admin/reportes" className={`admin-nav-link ${isActive('/admin/reportes')}`}>
                        Reportes
                    </Link>
                    <Link to="/admin/productos" className={`admin-nav-link ${isActive('/admin/productos')}`}>
                        Productos
                    </Link>
                    <Link to="/admin/ventas" className={`admin-nav-link ${isActive('/admin/ventas')}`}>
                        Ventas
                    </Link>
                </nav>

                {/* Menú de usuario */}
                <div className="admin-user">
                    <button
                        className="admin-user-button"
                        onClick={() => setMenuAbierto(!menuAbierto)}
                        type="button"
                    >
                        Bienvenido a Apotheclean, {usuario?.nombre}
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="6 9 12 15 18 9" />
                        </svg>
                    </button>

                    {menuAbierto && (
                        <div className="admin-user-menu">
                            <button onClick={handleLogout} className="admin-user-menu-item" type="button">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                    <polyline points="16 17 21 12 16 7" />
                                    <line x1="21" y1="12" x2="9" y2="12" />
                                </svg>
                                Cerrar sesión
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
